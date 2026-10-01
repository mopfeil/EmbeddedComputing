//! Shared setup for the networking examples: board start-up, Wi-Fi
//! connection to the Wokwi access point, DHCP, and a minimal MQTT client.
#![no_std]

pub mod mqtt;

use embassy_executor::Spawner;
use embassy_net::{Runner, Stack, StackResources};
use embassy_time::{Duration, Timer};
use esp_hal::{clock::CpuClock, peripherals::Peripherals, rng::Rng, timer::timg::TimerGroup};
use esp_println::println;
use esp_radio::wifi::{
    AuthenticationMethodConfig, Config, ControllerConfig, Interface, WifiController,
    sta::StationConfig,
};
use static_cell::StaticCell;

/// Open access point of the Wokwi simulator (no password, channel 6).
pub const SSID: &str = "Wokwi-GUEST";

/// Start the chip: clocks and heap (the Wi-Fi driver needs dynamic memory).
pub fn init() -> Peripherals {
    esp_println::logger::init_logger_from_env();
    let peripherals = esp_hal::init(esp_hal::Config::default().with_cpu_clock(CpuClock::max()));
    esp_alloc::heap_allocator!(#[esp_hal::ram(reclaimed)] size: 64 * 1024);
    peripherals
}

/// Start the task scheduler (esp-rtos). It needs a hardware timer and a
/// software interrupt; the Wi-Fi driver and embassy run on top of it.
pub fn start_scheduler(
    timg0: esp_hal::peripherals::TIMG0<'static>,
    sw_int: esp_hal::peripherals::FROM_CPU_INTR0<'static>,
) {
    let timg0 = TimerGroup::new(timg0);
    esp_rtos::start(timg0.timer0, sw_int);
}

/// Connect to the Wi-Fi network, start the IP stack and wait until DHCP
/// has delivered an address.
pub async fn connect_wifi(
    spawner: &Spawner,
    wifi: esp_hal::peripherals::WIFI<'static>,
) -> Stack<'static> {
    let station = Config::Station(
        StationConfig::default()
            .with_ssid(SSID.try_into().unwrap())
            .with_authentication(AuthenticationMethodConfig::Open)
            .with_channel(6),
    );
    let controller =
        WifiController::new(wifi, ControllerConfig::default().with_initial_config(station))
            .unwrap();

    // The IP stack (embassy-net, based on smoltcp) runs on top of the Wi-Fi interface.
    static RESOURCES: StaticCell<StackResources<4>> = StaticCell::new();
    let rng = Rng::new();
    let seed = (rng.random() as u64) << 32 | rng.random() as u64;
    let (stack, runner) = embassy_net::new(
        Interface::station(),
        embassy_net::Config::dhcpv4(Default::default()),
        RESOURCES.init(StackResources::new()),
        seed,
    );

    spawner.spawn(wifi_task(controller).unwrap());
    spawner.spawn(net_task(runner).unwrap());

    println!("Waiting for DHCP ...");
    stack.wait_config_up().await;
    stack
}

/// Keeps the Wi-Fi connection up: reconnects after a disconnect.
#[embassy_executor::task]
async fn wifi_task(mut controller: WifiController<'static>) {
    loop {
        match controller.connect_async().await {
            Ok(_) => {
                println!("Wi-Fi connected to {SSID}");
                let _ = controller.wait_for_disconnect_async().await;
                println!("Wi-Fi disconnected");
            }
            Err(e) => println!("Wi-Fi connect failed: {e:?}"),
        }
        Timer::after(Duration::from_secs(5)).await;
    }
}

/// Runs the IP stack: processes incoming and outgoing packets.
#[embassy_executor::task]
async fn net_task(mut runner: Runner<'static, Interface>) {
    runner.run().await
}
