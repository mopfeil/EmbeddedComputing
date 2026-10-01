//! Interrupt -> task: the task sleeps until the GPIO interrupt of the
//! button (GPIO5, to GND) wakes it up. No polling, no flag variable.
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_time::Timer;
use esp_backtrace as _;
use esp_hal::gpio::{Input, InputConfig, Level, Output, OutputConfig, Pull};
use esp_hal::timer::timg::TimerGroup;
use esp_println::println;

esp_bootloader_esp_idf::esp_app_desc!();

#[esp_rtos::main]
async fn main(_spawner: Spawner) -> ! {
    let peripherals = esp_hal::init(esp_hal::Config::default());
    let timg0 = TimerGroup::new(peripherals.TIMG0);
    esp_rtos::start(timg0.timer0, peripherals.FROM_CPU_INTR0);

    let mut led = Output::new(peripherals.GPIO4, Level::Low, OutputConfig::default());
    let mut button = Input::new(peripherals.GPIO5, InputConfig::default().with_pull(Pull::Up));

    let mut presses = 0;
    loop {
        // Enables the edge interrupt and suspends this task. The interrupt
        // handler of esp-hal wakes the task up again.
        button.wait_for_falling_edge().await;
        presses += 1;
        led.toggle();
        println!("button pressed ({presses})");

        Timer::after_millis(50).await; // debounce: ignore the bouncing
        button.wait_for_high().await; // wait until released
        Timer::after_millis(50).await;
    }
}
