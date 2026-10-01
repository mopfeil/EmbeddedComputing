# Example for chapter "Modelling"

The coffee machine state machine (Moore machine) on a Raspberry Pi Pico in Wokwi.
Circuit (`diagram.json`): buttons LEFT (GP10), RIGHT (GP11), READY (GP12) to GND,
LEDs COFFEE (GP16), MILK (GP17), SUGAR (GP18), serial monitor on UART0.

| Folder | Content |
|---|---|
| `c/coffee_fsm` | the state machine from the lecture in C (`switch`, state table, output table) - browser |
| `coffee-fsm` | the same state machine as a hardware independent Rust library with unit tests |
| `pico-rust` | Rust program for the Pico that uses `coffee-fsm` - Wokwi for VS Code |

```sh
cd coffee-fsm && cargo test           # 4 tests on the PC / Replit
cd pico-rust && cargo build --release
```

## Tested

Wokwi scenario LEFT, RIGHT, RIGHT, READY (C and Rust, two runs each):
idle -> coffee+milk -> coffee+milk+sugar -> make coffee+milk+sugar (all three
LEDs on) -> idle (all LEDs off).
