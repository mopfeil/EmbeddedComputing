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

A logic analyzer records on channels D0..D7: UART_TX (GP0), SDA (GP4), SCL (GP5),
SCK (GP18), COPI (GP19), LATCH (GP17), LED/PWM (GP15) and BUTTON (GP14).

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

## Tested in the simulator

Checked with `wokwi-cli` 0.27 in October 2026 (C and Rust unless noted):

| Example | Check | Result |
|---|---|---|
| gpio_blink | LED pin level over time | toggles every 500 ms |
| button_debounce | scenario: press twice | LED on, then off |
| button_irq (C) | scenario: one press | > 30 interrupts (bouncing!) |
| adc_uart | serial output | values printed, see below |
| uart_echo | serial output | ready message |
| i2c_mpu6050 | serial output | WHO_AM_I = 0x68, az = 1000 mg |
| spi_shift_register | 74HC595 outputs | exactly one output high |
| watchdog | scenario: hold button | no reset, see below |

Not run in the simulator: `gpio_blink_registers`, `pwm_fade`, `button_irq` (Rust).

Two limitations of the simulation showed up:

* The RP2040 **temperature sensor** is not simulated: it reads 0, which the
  formula turns into about 437 degrees C. A nice reason to check values for plausibility.
* The **watchdog reset** did not happen in the simulation (the program keeps
  hanging in the loop). Run `watchdog` on a real Pico to see the reset.
