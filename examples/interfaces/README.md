# Examples for chapter "Peripherals and Interfaces"

All examples run on a simulated Raspberry Pi Pico (RP2040) in [Wokwi](https://wokwi.com).
The C and the Rust examples use the same circuit (`diagram.json`):

| Pico pin | Connected to | Used by |
|---|---|---|
| GP0 / GP1 | Serial monitor (UART0 TX / RX) | adc_uart, uart_echo, i2c_mpu6050, watchdog, button_irq |
| GP4 / GP5 | MPU6050 SDA / SCL (I2C0) | i2c_mpu6050 |
| GP14 | Push button to GND | button_debounce, button_irq, watchdog |
| GP15 | LED with 220 Ohm resistor | gpio_blink, button_*, pwm_fade, watchdog |
| GP17 / GP18 / GP19 | 74HC595 STCP / SHCP / DS (SPI0) with LED bar | spi_shift_register |
| GP26 | Potentiometer (ADC0) | adc_uart |
| GP25 | On-board LED | gpio_blink_registers (Rust) |

A logic analyzer records UART_TX, SDA, SCL, SCK, COPI, LATCH, LED_PWM and BUTTON.

## C (in the browser)

1. Open <https://wokwi.com/projects/new/pi-pico> (Arduino template).
2. Replace `sketch.ino` with the example's `.ino` file.
3. Replace `diagram.json` with `c/diagram.json`.
4. Start the simulation. Output appears in the serial monitor.

The sketches use the Pico SDK functions (`hardware/gpio.h`, `hardware/pwm.h`, ...),
which are available because Wokwi runs the Arduino-Pico core on top of the SDK.

## Rust (local build, simulation in VS Code)

Wokwi no longer compiles Rust online, so the build is done locally:

```sh
rustup target add thumbv6m-none-eabi     # Cortex-M0+
cd rust
cargo build --release
```

Then install the *Wokwi Simulator* extension in VS Code, set the example in
`wokwi.toml` (`firmware` and `elf`) and run **F1 → Wokwi: Start Simulator**.
For debugging use **Wokwi: Start Simulator and Wait for Debugger** and connect
GDB to port 3333.

| Example | Topic |
|---|---|
| `gpio_blink` | GPIO output with the HAL |
| `gpio_blink_registers` | the same with raw register accesses |
| `button_debounce` | GPIO input, pull-up, software debouncing |
| `button_irq` | GPIO interrupt, sharing data with an ISR |
| `pwm_fade` | PWM slice, divider, TOP, duty cycle |
| `adc_uart` | ADC, temperature sensor, UART output |
| `uart_echo` | UART receive and transmit |
| `i2c_mpu6050` | I2C register read/write, repeated start |
| `spi_shift_register` | SPI mode 0, 74HC595 |
| `watchdog` | watchdog timeout and reset reason |
