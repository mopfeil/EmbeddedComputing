//! Given: the hardware of the ET1 lab set-up (see diagram.json).
//! You do not need to change this file.
//!
//!   GP7  red LED (high = on)          GP5  START button to GND (low = pressed)
//!   GP18 ENA  left motor PWM          GP19 ENB  right motor PWM   (PWM slice 1, 1 kHz)
//!   GP17 IN1  left direction A        GP20 IN3  right direction A
//!   GP16 IN2  left direction B        GP21 IN4  right direction B
//!   GP0/GP1  UART0, 115200 baud, to the serial monitor

use embedded_hal::delay::DelayNs;
use embedded_hal::digital::InputPin;
use rp_pico::hal::fugit::RateExtU32;
use rp_pico::hal::gpio::{self, DynPinId, FunctionSioInput, FunctionSioOutput, Pin, PullDown, PullUp};
use rp_pico::hal::pwm::{FreeRunning, Pwm1, Slice};
use rp_pico::hal::uart::{DataBits, Enabled, StopBits, UartConfig, UartPeripheral};
use rp_pico::hal::{self, Clock, pac};

pub type OutPin = Pin<DynPinId, FunctionSioOutput, PullDown>;
pub type InPin = Pin<DynPinId, FunctionSioInput, PullUp>;
pub type Uart = UartPeripheral<
    Enabled,
    pac::UART0,
    (
        Pin<gpio::bank0::Gpio0, gpio::FunctionUart, PullDown>,
        Pin<gpio::bank0::Gpio1, gpio::FunctionUart, PullDown>,
    ),
>;

pub struct Board {
    pub led: OutPin,
    pub button: InPin,
    /// PWM slice 1: `pwm.channel_a` drives ENA (left), `pwm.channel_b` ENB (right).
    /// Duty cycle with embedded-hal's SetDutyCycle: `set_duty_cycle_percent(0..=100)`.
    pub pwm: Slice<Pwm1, FreeRunning>,
    pub in1: OutPin,
    pub in2: OutPin,
    pub in3: OutPin,
    pub in4: OutPin,
    /// For `writeln!(board.uart, "...")` (needs `use core::fmt::Write`).
    pub uart: Uart,
    timer: hal::Timer,
}

impl Board {
    pub fn init() -> Board {
        let mut pac = pac::Peripherals::take().unwrap();
        let mut watchdog = hal::Watchdog::new(pac.WATCHDOG);
        let clocks = hal::clocks::init_clocks_and_plls(
            rp_pico::XOSC_CRYSTAL_FREQ, pac.XOSC, pac.CLOCKS, pac.PLL_SYS, pac.PLL_USB,
            &mut pac.RESETS, &mut watchdog,
        )
        .ok()
        .unwrap();
        let timer = hal::Timer::new(pac.TIMER, &mut pac.RESETS, &clocks);
        let sio = hal::Sio::new(pac.SIO);
        let pins = rp_pico::Pins::new(pac.IO_BANK0, pac.PADS_BANK0, sio.gpio_bank0, &mut pac.RESETS);

        let uart_pins = (
            pins.gpio0.into_function::<gpio::FunctionUart>(),
            pins.gpio1.into_function::<gpio::FunctionUart>(),
        );
        let uart = UartPeripheral::new(pac.UART0, uart_pins, &mut pac.RESETS)
            .enable(
                UartConfig::new(115_200.Hz(), DataBits::Eight, None, StopBits::One),
                clocks.peripheral_clock.freq(),
            )
            .unwrap();

        let slices = hal::pwm::Slices::new(pac.PWM, &mut pac.RESETS);
        let mut pwm = slices.pwm1;
        pwm.set_div_int(125); // 125 MHz / 125 = 1 MHz counter clock
        pwm.set_top(999); // 1000 counts -> 1 kHz
        pwm.enable();
        pwm.channel_a.output_to(pins.gpio18);
        pwm.channel_b.output_to(pins.gpio19);

        Board {
            led: pins.gpio7.into_push_pull_output().into_dyn_pin(),
            button: pins.gpio5.into_pull_up_input().into_dyn_pin(),
            pwm,
            in1: pins.gpio17.into_push_pull_output().into_dyn_pin(),
            in2: pins.gpio16.into_push_pull_output().into_dyn_pin(),
            in3: pins.gpio20.into_push_pull_output().into_dyn_pin(),
            in4: pins.gpio21.into_push_pull_output().into_dyn_pin(),
            uart,
            timer,
        }
    }

    /// Milliseconds since start.
    pub fn millis(&self) -> u64 {
        self.timer.get_counter().ticks() / 1000
    }

    pub fn delay_ms(&mut self, ms: u32) {
        self.timer.delay_ms(ms);
    }

    /// Raw level of the button, without debouncing: true = pressed.
    pub fn button_down(&mut self) -> bool {
        self.button.is_low().unwrap()
    }
}
