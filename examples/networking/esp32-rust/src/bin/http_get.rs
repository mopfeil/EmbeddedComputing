//! HTTP by hand: resolve a name with DNS, open a TCP connection to port 80,
//! send the request text and print the response.
#![no_std]
#![no_main]

use embassy_executor::Spawner;
use embassy_net::{dns::DnsQueryType, tcp::TcpSocket};
use embassy_time::{Duration, Timer};
use embedded_io_async::Write;
use esp_backtrace as _;
use esp_println::{print, println};

esp_bootloader_esp_idf::esp_app_desc!();

const HOST: &str = "example.com";

#[esp_rtos::main]
async fn main(spawner: Spawner) -> ! {
    let peripherals = esp32_networking::init();
    esp32_networking::start_scheduler(peripherals.TIMG0, peripherals.FROM_CPU_INTR0);
    let stack = esp32_networking::connect_wifi(&spawner, peripherals.WIFI).await;

    // DNS: name -> IPv4 address (UDP request to the DNS server from DHCP)
    let addr = stack.dns_query(HOST, DnsQueryType::A).await.unwrap()[0];
    println!("{HOST} = {addr}");

    // TCP: the socket needs buffers for received and not yet acknowledged data
    let mut rx_buf = [0u8; 2048];
    let mut tx_buf = [0u8; 512];
    let mut socket = TcpSocket::new(stack, &mut rx_buf, &mut tx_buf);
    socket.set_timeout(Some(Duration::from_secs(10)));
    socket.connect((addr, 80)).await.unwrap(); // three-way handshake
    println!("connected to {:?}", socket.remote_endpoint());

    // HTTP/1.1 request: request line, header lines, empty line
    let request = "GET / HTTP/1.1\r\nHost: example.com\r\nConnection: close\r\n\r\n";
    socket.write_all(request.as_bytes()).await.unwrap();

    // Read until the server closes the connection (read returns 0).
    let mut buf = [0u8; 512];
    loop {
        match socket.read(&mut buf).await {
            Ok(0) | Err(_) => break,
            Ok(n) => print!("{}", core::str::from_utf8(&buf[..n]).unwrap_or("<binary>")),
        }
    }
    socket.close();
    println!("\n--- connection closed");

    loop {
        Timer::after(Duration::from_secs(10)).await;
    }
}
