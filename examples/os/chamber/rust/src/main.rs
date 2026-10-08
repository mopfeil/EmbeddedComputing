//! Climate chamber in Rust (Embassy): the same program as chamber.ino.
//! The ESP32-C3 holds the temperature of a chamber at 40 degC. Chamber and
//! fan are custom chips in the simulator (../chips): the program sees them
//! only through its interfaces.
//!
//!   I2C  (SDA 8, SCL 9, 100 kHz)  TMP102-like sensor 0x48, LCD 0x27
//!   PWM  GPIO6 heater, GPIO7 fan (LEDC, 1 kHz, 10 bit)
//!   GPIO5 fan tachometer, 2 pulses per revolution
//!   GPIO10 alarm LED
//!
//! Tasks (one executor: no priorities, every task runs until its next .await)
//!   main     PI controller, safe state on faults  <- channel from sensor
//!   sensor   reads the temperature every 100 ms   -> channel to main
//!   tach     counts the tachometer edges
//!   fan      rpm every 500 ms, stall detection    -> fault bits
//!   display  LCD and serial log every 500 ms      <- status "mailbox"
//! The sensor and the display share the I2C bus through an async Mutex.
#![no_std]
#![no_main]

mod lcd;

use core::cell::Cell;
use core::fmt::Write;
use embassy_executor::Spawner;
use embassy_sync::blocking_mutex::Mutex as BlockingMutex;
use embassy_sync::blocking_mutex::raw::{CriticalSectionRawMutex, NoopRawMutex};
use embassy_sync::channel::Channel;
use embassy_sync::mutex::Mutex;
use embassy_time::{Duration, Instant, Ticker, with_timeout};
use esp_backtrace as _;
use esp_hal::Blocking;
use esp_hal::gpio::{DriveMode, Input, InputConfig, Level, Output, OutputConfig, Pull};
use esp_hal::i2c::master::{Config as I2cConfig, I2c};
use esp_hal::ledc::channel::{self, ChannelHW, ChannelIFace};
use esp_hal::ledc::timer::{self, TimerIFace};
use esp_hal::ledc::{LSGlobalClkSource, Ledc, LowSpeed};
use esp_hal::time::Rate;
use esp_hal::timer::timg::TimerGroup;
use esp_println::println;
use static_cell::StaticCell;

esp_bootloader_esp_idf::esp_app_desc!();

const TMP102: u8 = 0x48;
const SETPOINT: f32 = 40.0; // degC
const KP: f32 = 0.1; // PI controller, output 0..1
const KI: f32 = 0.02;

const FAN_STALL: u8 = 1 << 0;
const SENSOR_LOST: u8 = 1 << 1;

#[derive(Clone, Copy)]
struct Status {
    temp: f32,
    heat: f32,
    fan: f32,
    rpm: u32,
    faults: u8,
}

/// One bus, two users: the async Mutex makes a whole transfer sequence
/// exclusive. The bus lives in a StaticCell, the tasks get a &'static
/// reference. The I2C driver itself is the blocking one: one transfer takes
/// at most 0.5 ms, and in Wokwi the async driver of esp-hal 1.2 stalled the
/// whole executor at the first transfer.
type I2cBus = Mutex<NoopRawMutex, I2c<'static, Blocking>>;
static I2C: StaticCell<I2cBus> = StaticCell::new();
/// sensor -> control, like the FreeRTOS queue
static MEASUREMENTS: Channel<CriticalSectionRawMutex, f32, 4> = Channel::new();
/// Small shared values: a critical section around a Cell (no atomics on the ESP32-C3)
static PULSES: BlockingMutex<CriticalSectionRawMutex, Cell<u32>> = BlockingMutex::new(Cell::new(0));
static RPM: BlockingMutex<CriticalSectionRawMutex, Cell<u32>> = BlockingMutex::new(Cell::new(0));
static FAN_DEMAND: BlockingMutex<CriticalSectionRawMutex, Cell<f32>> = BlockingMutex::new(Cell::new(0.0));
/// fault bits, like the FreeRTOS event group
static FAULTS: BlockingMutex<CriticalSectionRawMutex, Cell<u8>> = BlockingMutex::new(Cell::new(0));
/// control -> display: always the latest status, like xQueueOverwrite
static STATUS: BlockingMutex<CriticalSectionRawMutex, Cell<Option<Status>>> =
    BlockingMutex::new(Cell::new(None));

fn set_fault(bit: u8, on: bool) {
    FAULTS.lock(|f| f.set(if on { f.get() | bit } else { f.get() & !bit }));
}

/// Reads the temperature register of the TMP102: pointer 0, then two bytes.
/// Every error is passed on -- the caller has to decide.
async fn read_temperature(bus: &I2cBus) -> Result<f32, esp_hal::i2c::master::Error> {
    let mut i2c = bus.lock().await;
    let mut buf = [0u8; 2];
    i2c.write_read(TMP102, &[0x00], &mut buf)?;
    let raw = i16::from_be_bytes(buf) >> 4; // 12 bit, 0.0625 degC per LSB
    Ok(raw as f32 * 0.0625)
}

#[embassy_executor::task]
async fn sensor(bus: &'static I2cBus) {
    let mut ticker = Ticker::every(Duration::from_millis(100));
    loop {
        if let Ok(temp) = read_temperature(bus).await {
            let _ = MEASUREMENTS.try_send(temp);
        }
        ticker.next().await;
    }
}

#[embassy_executor::task]
async fn tach(mut pin: Input<'static>) {
    loop {
        pin.wait_for_rising_edge().await; // the GPIO interrupt wakes this task
        PULSES.lock(|p| p.set(p.get() + 1));
    }
}

#[embassy_executor::task]
async fn fan() {
    let mut ticker = Ticker::every(Duration::from_millis(500));
    let mut slow = 0;
    loop {
        ticker.next().await;
        let pulses = PULSES.lock(|p| p.replace(0));
        let rpm = pulses * 60; // pulses / 2 per rev / 0.5 s * 60 s
        RPM.lock(|r| r.set(rpm));
        // stalled: the fan is driven, but turns too slowly for 1 s
        let demand = FAN_DEMAND.lock(|d| d.get());
        slow = if demand > 0.2 && rpm < 300 { slow + 1 } else { 0 };
        if slow >= 2 {
            set_fault(FAN_STALL, true);
        } else if rpm >= 300 {
            set_fault(FAN_STALL, false);
        }
    }
}

#[embassy_executor::task]
async fn display(bus: &'static I2cBus) {
    lcd::init(&mut *bus.lock().await).await.ok();
    let mut ticker = Ticker::every(Duration::from_millis(500));
    loop {
        if let Some(s) = STATUS.lock(|c| c.get()) {
            println!(
                "{},{:.2},{:.2},{:.2},{},{}",
                Instant::now().as_millis(),
                s.temp,
                s.heat,
                s.fan,
                s.rpm,
                s.faults
            );
            let mut line1 = lcd::Line::new();
            let mut line2 = lcd::Line::new();
            let _ = write!(line1, "T {:5.1}C set {:2.0}", s.temp, SETPOINT);
            let _ = if s.faults & FAN_STALL != 0 {
                write!(line2, "FAN STALLED!")
            } else if s.faults & SENSOR_LOST != 0 {
                write!(line2, "SENSOR LOST!")
            } else {
                write!(line2, "H{:3}% F{:4}rpm", (s.heat * 100.0) as u32, s.rpm)
            };
            let mut i2c = bus.lock().await;
            lcd::print_at(&mut i2c, 0, line1.bytes()).await.ok();
            lcd::print_at(&mut i2c, 1, line2.bytes()).await.ok();
        }
        ticker.next().await;
    }
}

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp_hal::init(esp_hal::Config::default());
    let timg0 = TimerGroup::new(peripherals.TIMG0);
    esp_rtos::start(timg0.timer0, peripherals.FROM_CPU_INTR0);

    let i2c = I2c::new(peripherals.I2C0, I2cConfig::default().with_frequency(Rate::from_khz(100)))
        .unwrap()
        .with_sda(peripherals.GPIO8)
        .with_scl(peripherals.GPIO9);
    let bus = I2C.init(Mutex::new(i2c));

    // PWM: one LEDC timer (1 kHz, 10 bit), two channels
    let mut ledc = Ledc::new(peripherals.LEDC);
    ledc.set_global_slow_clock(LSGlobalClkSource::APBClk);
    let mut pwm_timer = ledc.timer::<LowSpeed>(timer::Number::Timer0);
    pwm_timer
        .configure(timer::config::Config {
            duty: timer::config::Duty::Duty10Bit,
            clock_source: timer::LSClockSource::APBClk,
            frequency: Rate::from_khz(1),
        })
        .unwrap();
    let mut heater = ledc.channel(channel::Number::Channel0, peripherals.GPIO6);
    let mut fan_pwm = ledc.channel(channel::Number::Channel1, peripherals.GPIO7);
    for ch in [&mut heater, &mut fan_pwm] {
        ch.configure(channel::config::Config {
            timer: &pwm_timer,
            duty_pct: 0,
            drive_mode: DriveMode::PushPull,
        })
        .unwrap();
    }
    let mut alarm = Output::new(peripherals.GPIO10, Level::Low, OutputConfig::default());
    let tach_pin = Input::new(peripherals.GPIO5, InputConfig::default().with_pull(Pull::Up));

    println!("t_ms,temp,heat,fan,rpm,faults");
    spawner.spawn(sensor(bus).unwrap());
    spawner.spawn(tach(tach_pin).unwrap());
    spawner.spawn(fan().unwrap());
    spawner.spawn(display(bus).unwrap());

    // the control loop runs in main: it owns the PWM channels and the LED
    let mut integral = 0.0f32;
    let mut temp = 0.0f32;
    loop {
        match with_timeout(Duration::from_millis(500), MEASUREMENTS.receive()).await {
            Ok(t) => {
                temp = t;
                set_fault(SENSOR_LOST, false);
            }
            Err(_) => set_fault(SENSOR_LOST, true), // no value for 500 ms
        }
        let faults = FAULTS.lock(|f| f.get());

        let (heat, fan) = if faults != 0 {
            integral = 0.0; // safe state: heater off, full air
            (0.0, 1.0)
        } else {
            let error = SETPOINT - temp;
            let u = KP * error + KI * integral;
            if (u > 0.0 && u < 1.0) || (u >= 1.0 && error < 0.0) || (u <= 0.0 && error > 0.0) {
                integral += error * 0.1; // anti-windup: integrate only when useful
            }
            (u.clamp(0.0, 1.0), if temp > SETPOINT + 3.0 { 1.0 } else { 0.4 })
        };
        heater.set_duty_hw((heat * 1023.0) as u32);
        fan_pwm.set_duty_hw((fan * 1023.0) as u32);
        FAN_DEMAND.lock(|d| d.set(fan));
        alarm.set_level(if faults != 0 { Level::High } else { Level::Low });

        let rpm = RPM.lock(|r| r.get());
        STATUS.lock(|c| c.set(Some(Status { temp, heat, fan, rpm, faults })));
    }
}
