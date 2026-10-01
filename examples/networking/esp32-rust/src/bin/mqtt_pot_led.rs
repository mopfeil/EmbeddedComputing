//! MQTT: publish the potentiometer value (GPIO2, ADC) every 2 s and switch
//! the LED (GPIO4) with messages "on" / "off" on the topic .../led.
//! Change DEVICE to a unique name - the public broker is shared with everybody!
#![no_std]
#![no_main]

use core::fmt::Write as _;
use embassy_executor::Spawner;
use embassy_futures::select::{Either, select};
use embassy_net::{dns::DnsQueryType, tcp::TcpSocket};
use embassy_time::{Duration, Instant, Timer};
use esp_backtrace as _;
use esp_hal::analog::adc::{Adc, AdcConfig, Attenuation};
use esp_hal::gpio::{Level, Output, OutputConfig};
use esp_println::println;
use esp32_networking::mqtt;

esp_bootloader_esp_idf::esp_app_desc!();

const BROKER: &str = "test.mosquitto.org";
const DEVICE: &str = "rwu-ec-demo"; // <- change me
const TOPIC_POT: &str = "rwu-ec/rwu-ec-demo/pot";
const TOPIC_LED: &str = "rwu-ec/rwu-ec-demo/led";

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp32_networking::init();
    esp32_networking::start_scheduler(peripherals.TIMG0, peripherals.FROM_CPU_INTR0);
    let mut led = Output::new(peripherals.GPIO4, Level::Low, OutputConfig::default());
    let mut adc_config = AdcConfig::new();
    let mut pot = adc_config.enable_pin(peripherals.GPIO2, Attenuation::_11dB);
    let mut adc = Adc::new(peripherals.ADC1, adc_config);

    let stack = esp32_networking::connect_wifi(&spawner, peripherals.WIFI).await;
    let broker = stack.dns_query(BROKER, DnsQueryType::A).await.unwrap()[0];

    let mut rx_buf = [0u8; 1024];
    let mut tx_buf = [0u8; 1024];
    let mut socket = TcpSocket::new(stack, &mut rx_buf, &mut tx_buf);
    socket.connect((broker, 1883)).await.unwrap(); // MQTT without TLS
    mqtt::connect(&mut socket, DEVICE).await.unwrap();
    mqtt::subscribe(&mut socket, TOPIC_LED).await.unwrap();
    println!("connected to {BROKER}, subscribed to {TOPIC_LED}");

    let mut next_publish = Instant::now();
    let mut packet = [0u8; 256];
    loop {
        // Wait for whatever comes first: an incoming packet or the publish time.
        match select(mqtt::receive(&mut socket, &mut packet), Timer::at(next_publish)).await {
            Either::First(Ok((header, len))) => {
                if mqtt::packet_type(header) == 3 {
                    if let Some((topic, payload)) = mqtt::parse_publish(&packet[..len]) {
                        println!("received {topic}: {:?}", core::str::from_utf8(payload));
                        match payload {
                            b"on" => led.set_high(),
                            b"off" => led.set_low(),
                            _ => {}
                        }
                    }
                }
            }
            Either::First(Err(e)) => panic!("MQTT connection lost: {e:?}"),
            Either::Second(()) => {
                let raw: u16 = nb::block!(adc.read_oneshot(&mut pot)).unwrap();
                let mut text = heapless_string();
                write!(text, "{raw}").unwrap();
                mqtt::publish(&mut socket, TOPIC_POT, text.as_bytes()).await.unwrap();
                println!("published {TOPIC_POT} = {raw}");
                next_publish += Duration::from_secs(2);
            }
        }
    }
}

/// A tiny fixed-size string for formatting numbers without a heap.
fn heapless_string() -> FixedString {
    FixedString { buf: [0; 16], len: 0 }
}

struct FixedString {
    buf: [u8; 16],
    len: usize,
}

impl FixedString {
    fn as_bytes(&self) -> &[u8] {
        &self.buf[..self.len]
    }
}

impl core::fmt::Write for FixedString {
    fn write_str(&mut self, s: &str) -> core::fmt::Result {
        let end = self.len + s.len();
        self.buf.get_mut(self.len..end).ok_or(core::fmt::Error)?.copy_from_slice(s.as_bytes());
        self.len = end;
        Ok(())
    }
}
