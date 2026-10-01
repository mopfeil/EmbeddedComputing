//! UDP: ask a time server (NTP, port 123) for the current time.
//! One request datagram, one answer datagram - no connection.
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_net::{
    dns::DnsQueryType,
    udp::{PacketMetadata, UdpSocket},
};
use embassy_time::{Duration, Timer, with_timeout};
use esp_backtrace as _;
use esp_println::println;

esp_bootloader_esp_idf::esp_app_desc!();

const NTP_SERVER: &str = "pool.ntp.org";
const NTP_TO_UNIX: u64 = 2_208_988_800; // seconds from 1900-01-01 to 1970-01-01

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp32_networking::init();
    esp32_networking::start_scheduler(peripherals.TIMG0, peripherals.FROM_CPU_INTR0);
    let stack = esp32_networking::connect_wifi(&spawner, peripherals.WIFI).await;

    let server = stack.dns_query(NTP_SERVER, DnsQueryType::A).await.unwrap()[0];

    let mut rx_meta = [PacketMetadata::EMPTY; 4];
    let mut rx_buf = [0u8; 256];
    let mut tx_meta = [PacketMetadata::EMPTY; 4];
    let mut tx_buf = [0u8; 256];
    let mut socket = UdpSocket::new(stack, &mut rx_meta, &mut rx_buf, &mut tx_meta, &mut tx_buf);
    socket.bind(12345).unwrap(); // local port

    loop {
        // 48 byte NTP packet: first byte = LI 0, version 4, mode 3 (client)
        let mut request = [0u8; 48];
        request[0] = 0b00_100_011;
        socket.send_to(&request, (server, 123)).await.unwrap();

        // UDP gives no guarantee: the answer may never arrive -> timeout
        let mut answer = [0u8; 48];
        match with_timeout(Duration::from_secs(3), socket.recv_from(&mut answer)).await {
            Ok(Ok((48, from))) => {
                // Transmit timestamp: seconds since 1900 in bytes 40..44 (big endian)
                let secs = u32::from_be_bytes(answer[40..44].try_into().unwrap()) as u64;
                let unix = secs - NTP_TO_UNIX;
                let (h, m, s) = ((unix / 3600) % 24, (unix / 60) % 60, unix % 60);
                println!("{from}: unix time {unix}, UTC {h:02}:{m:02}:{s:02}");
            }
            Ok(_) => println!("unexpected answer"),
            Err(_) => println!("no answer within 3 s (UDP datagram lost?)"),
        }
        Timer::after(Duration::from_secs(10)).await;
    }
}
