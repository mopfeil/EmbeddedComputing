# Examples for chapter "Operating Systems"

ESP32-C3 in Wokwi. Circuit (`diagram.json`): LED on GPIO4, potentiometer on
GPIO2 (ADC1), push button on GPIO5 to GND, serial monitor on TX/RX.

The **C** examples use FreeRTOS, which the Arduino core for the ESP32 is
built on (open a new ESP32-C3 project on <https://wokwi.com/projects/new/esp32-c3>,
replace `sketch.ino` and `diagram.json`). The **Rust** examples use the async
framework Embassy on top of `esp-hal` (local build, simulation with Wokwi for
VS Code, see `esp32-rust/wokwi.toml`).

| Topic | C (FreeRTOS) | Rust (Embassy) |
|---|---|---|
| two periodic tasks | `tasks` – `xTaskCreate`, `xTaskDelayUntil` | `tasks` – `#[task]`, `Ticker` |
| message queue | `queue` – `xQueueSend`/`xQueueReceive` | `queue` – `Channel` |
| interrupt → task | `button_isr` – binary semaphore, `...FromISR` | `button_isr` – `wait_for_falling_edge().await` |
| shared data | `race_mutex` – lost updates, then a mutex | `mutex` – async `Mutex` |
| priority inversion | `priority_inversion` – semaphore vs. mutex | – (one executor has no priorities) |

Case study **`chamber/`**: FreeRTOS program plus two custom chips that model
the environment (thermal plant with I2C sensor, fan with tachometer), I2C LCD,
logic analyzer and a fault injection scenario. C only. Its own `diagram.json`
and README.

```sh
cd esp32-rust
cargo build --release      # needs: rustup target add riscv32imc-unknown-none-elf
```

## Tested

All examples were run with `wokwi-cli` 0.27 in October 2026:

| Example | Result in the simulator |
|---|---|
| tasks | heartbeat exactly every 1000 ms (C and Rust) |
| queue | averages printed (C and Rust) |
| button_isr | scenario with two bouncing presses: exactly 2 counted (C and Rust) |
| race_mutex (C) | without mutex: **1001** instead of 2000; with mutex: 2000 |
| mutex (Rust) | 2000 |
| priority_inversion (C) | binary semaphore: H waits **550 ms**; mutex: H waits **251 ms** |
| chamber (C) | 40.00 °C; fan stall alarm after 2.0 s, sensor loss after 0.5 s (see `chamber/README.md`) |

Note for `race_mutex` and `priority_inversion`: `setup()` runs in the Arduino
loop task with priority 1. It raises its own priority first, so that all
tasks exist before the first of them starts.
