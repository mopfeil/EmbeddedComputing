# Example for chapter "Introduction"

A coffee machine as a first embedded system, on an Arduino Uno in Wokwi. The
machine itself (water boiler, heater, pump) is a **custom chip**: a small C
program with a physical model that the simulator runs next to the Uno.

| File | Content |
|---|---|
| `coffee/sketch.ino` | the program: two-point control of the water temperature, button "coffee", LED "ready" |
| `coffee/coffee.chip.c`, `coffee/coffee.chip.json` | the machine: heat balance of 100 ml water, 1200 W heater, pump 2 ml/s, sensor 10 mV/°C; the chip shows the cup filling |
| `coffee/diagram.json` | Uno, the chip, button, LEDs "ready" (pin 7) and "heater" (pin 8) |
| `coffee-rust/` | the same program in Rust with `arduino-hal` (avr-hal) - Wokwi for VS Code |

Model of the chip, every 10 ms:

    m c dT/dt = P_heater - k (T - T_room) - flow c (T - T_room)

## Run in the browser

Open a new Arduino Uno project on <https://wokwi.com/projects/new/arduino-uno>,
replace `sketch.ino` and `diagram.json`, then add the custom chip: file menu
"New file…" → "Custom chip (C)", name it `coffee`, and paste the content of
`coffee.chip.c` and `coffee.chip.json`. Wokwi compiles the chip in the browser.

Wait for the green LED (about 25 s), then press the button: the pump runs for
20 s and the cup on the chip fills up.

## Rust version

```sh
cd coffee-rust
cargo build --release     # nightly from rust-toolchain.toml, needs avr-gcc as linker
wokwi-cli chip compile ../coffee/coffee.chip.c -o ../coffee/coffee.chip.wasm
```

`avr-gcc` comes with the Arduino AVR core (`~/.arduino15/packages/arduino/tools/avr-gcc/*/bin`,
add it to `PATH`) or from the package `gcc-avr`. Differences to the C version:
temperatures are integers in tenths of a degree (no floating point unit, and
`ufmt` prints no floats), and the time is counted in 10 ms loop cycles instead
of `millis()`. `Cargo.lock` pins `encoding_rs` to 0.8.35, because newer
versions do not build with the nightly from the avr-hal template.

## Tested

With `wokwi-cli` 0.28.1 and arduino:avr 1.8.8 in October 2026, scenario:
button at 34 °C → "please wait, water at 34.2 C"; ready after about 27 s
(93.8 °C, heater off); button → pump 20 s, water stays between 91 and 94 °C,
"enjoy your coffee!". The Rust version (2.9 KB) gives the same output with
the same scenario. The cup drawing on the chip was not checked
(`wokwi-cli` cannot take screenshots of custom chips).

Why an Uno and not a Pico: the Uno's ADC uses 5 V as reference. On the
simulated Pico, a voltage from a custom chip was measured against 5 V instead
of the real Pico's 3.3 V (1.0 V gave 819 instead of 1241), so the 3.3 V
conversion would show wrong temperatures there.
