//! Two independent tasks with different periods: a blinking LED (GPIO4)
//! and a heartbeat message on the serial monitor.
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_time::{Duration, Instant, Ticker};
use esp_backtrace as _;
use esp_hal::gpio::{Level, Output, OutputConfig};
use esp_hal::timer::timg::TimerGroup;
use esp_println::println;

esp_bootloader_esp_idf::esp_app_desc!();

/// A task is an async function. It runs until it awaits something and
/// then gives the CPU to the next ready task.
#[embassy_executor::task]
async fn blink(mut led: Output<'static>) {
    let mut ticker = Ticker::every(Duration::from_millis(500));
    loop {
        led.toggle();
        ticker.next().await; // fixed period, does not drift
    }
}

#[embassy_executor::task]
async fn heartbeat() {
    let mut ticker = Ticker::every(Duration::from_secs(1));
    for n in 0.. {
        println!("heartbeat {n} at {} ms", Instant::now().as_millis());
        ticker.next().await;
    }
}

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp_hal::init(esp_hal::Config::default());
    let timg0 = TimerGroup::new(peripherals.TIMG0);
    esp_rtos::start(timg0.timer0, peripherals.FROM_CPU_INTR0);

    let led = Output::new(peripherals.GPIO4, Level::Low, OutputConfig::default());
    spawner.spawn(blink(led).unwrap());
    spawner.spawn(heartbeat().unwrap());

    loop {
        // main is a task, too - here it has nothing more to do
        embassy_time::Timer::after_secs(3600).await;
    }
}
