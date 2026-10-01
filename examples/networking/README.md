# Examples for chapter "Networking (TCP/IP)"

## ESP32-C3 in Wokwi

The device examples run on a simulated ESP32-C3 (RISC-V) that connects to the
simulator's Wi-Fi access point **Wokwi-GUEST** (open, channel 6). Wokwi routes
its traffic to the internet, so DNS, HTTP, NTP and MQTT reach real servers.

Circuit (`diagram.json`): LED with 220 Ohm resistor on GPIO4, potentiometer on
GPIO2 (ADC1), serial monitor on TX/RX.

| Example | Layer / protocol | What it shows |
|---|---|---|
| `wifi_dhcp` | Wi-Fi, DHCP | MAC address, IP address, gateway, DNS server |
| `http_get` | DNS, TCP, HTTP | an HTTP/1.1 request written by hand |
| `udp_ntp` | UDP, NTP | one request datagram, one answer, timeout |
| `mqtt_pot_led` | TCP, MQTT | publish sensor values, subscribe to commands |

**C** (in the browser): new ESP32-C3 project on <https://wokwi.com/projects/new/esp32-c3>
(Arduino), replace `sketch.ino` and `diagram.json`. For `mqtt_pot_led` add the
library *PubSubClient* (Library Manager, or `libraries.txt`).

**Rust** (local build, simulation with Wokwi for VS Code):

```sh
rustup target add riscv32imc-unknown-none-elf
cd esp32-rust
cargo build --release
```

Set the example in `wokwi.toml` and start the simulator (F1 → Wokwi: Start Simulator).
The crate uses `esp-hal` 1.2, `esp-radio` (Wi-Fi driver), `esp-rtos` and
`embassy-net` (TCP/IP stack based on smoltcp). `src/lib.rs` contains the Wi-Fi
and DHCP setup used by all examples; `src/mqtt.rs` is a minimal MQTT client
written by hand to show the packet format.

**MQTT:** change `DEVICE` and the topics to a name of your own. The public
broker `test.mosquitto.org` is shared with the whole world, so do not send
anything private there. To switch the LED, publish `on` or `off` to
`rwu-ec/<your-device>/led`, e.g. with MQTT Explorer or
`mosquitto_pub -h test.mosquitto.org -t rwu-ec/<your-device>/led -m on`.

**Traffic analysis:** in the Wokwi web editor, the network traffic of a simulation can be
downloaded as a `.pcap` file and opened in Wireshark.

## Sockets on a PC (or Replit)

`host-c` and `host-rust` contain a TCP echo server and client written with the
BSD socket API (C) and the Rust standard library. Any combination works
(C server with Rust client and so on).

```sh
cd host-c
gcc -Wall -o tcp_echo_server tcp_echo_server.c && ./tcp_echo_server 5000 &
gcc -Wall -o tcp_echo_client tcp_echo_client.c && ./tcp_echo_client 127.0.0.1 5000 hello

cd host-rust
cargo run --bin tcp_echo_server -- 5000 &
cargo run --bin tcp_echo_client -- 127.0.0.1:5000 hello
```

## Tested

All ESP32-C3 examples were run with `wokwi-cli` 0.27 in October 2026 (C and Rust):
DHCP address 10.13.37.2/24, HTTP response from example.com, NTP time,
MQTT publish and receiving a command via a retained message. The host examples
were tested in all four combinations.

Observations from the tests:

* `test.mosquitto.org` sometimes drops a connection if the CONNECT packet
  arrives split into two TCP segments. The Rust MQTT code therefore sends every
  packet with a single write.
* The simulated RSSI is +3 dBm. On a real device, expect -30 to -90 dBm.
