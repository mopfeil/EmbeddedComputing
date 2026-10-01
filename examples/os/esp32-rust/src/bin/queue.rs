//! Producer / consumer with a channel (message queue):
//! main samples the potentiometer (ADC, GPIO2) every 100 ms and sends the
//! values; the consumer task averages 10 values and prints the result.
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_sync::blocking_mutex::raw::CriticalSectionRawMutex;
use embassy_sync::channel::Channel;
use embassy_time::{Duration, Ticker};
use esp_backtrace as _;
use esp_hal::analog::adc::{Adc, AdcConfig, Attenuation};
use esp_hal::timer::timg::TimerGroup;
use esp_println::println;

esp_bootloader_esp_idf::esp_app_desc!();

/// Queue for 8 values. A full queue makes send() wait (back pressure),
/// an empty queue makes receive() wait.
static SAMPLES: Channel<CriticalSectionRawMutex, u16, 8> = Channel::new();

#[embassy_executor::task]
async fn consumer() {
    loop {
        let mut sum: u32 = 0;
        for _ in 0..10 {
            sum += SAMPLES.receive().await as u32; // waits for the next value
        }
        println!("average of 10 samples: {}", sum / 10);
    }
}

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp_hal::init(esp_hal::Config::default());
    let timg0 = TimerGroup::new(peripherals.TIMG0);
    esp_rtos::start(timg0.timer0, peripherals.FROM_CPU_INTR0);

    let mut adc_config = AdcConfig::new();
    let mut pot = adc_config.enable_pin(peripherals.GPIO2, Attenuation::_11dB);
    let mut adc = Adc::new(peripherals.ADC1, adc_config);

    spawner.spawn(consumer().unwrap());

    let mut ticker = Ticker::every(Duration::from_millis(100));
    loop {
        let raw: u16 = nb::block!(adc.read_oneshot(&mut pot)).unwrap();
        SAMPLES.send(raw).await; // producer
        ticker.next().await;
    }
}
