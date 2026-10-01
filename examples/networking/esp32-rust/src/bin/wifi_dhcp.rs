//! Connect to Wi-Fi and show what DHCP has configured.
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_time::{Duration, Timer};
use esp_backtrace as _;
use esp_println::println;

esp_bootloader_esp_idf::esp_app_desc!();

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp32_networking::init();
    esp32_networking::start_scheduler(peripherals.TIMG0, peripherals.FROM_CPU_INTR0);
    let stack = esp32_networking::connect_wifi(&spawner, peripherals.WIFI).await;

    // Layer 2: our MAC address. Layer 3: what the DHCP server assigned.
    println!("MAC address : {}", stack.hardware_address());
    let config = stack.config_v4().unwrap();
    println!("IP address  : {}", config.address); // address/prefix, e.g. 10.10.0.2/24
    println!("Gateway     : {:?}", config.gateway);
    println!("DNS servers : {:?}", config.dns_servers);

    loop {
        Timer::after(Duration::from_secs(10)).await;
    }
}
