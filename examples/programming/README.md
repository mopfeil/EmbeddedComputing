# Examples for chapter "Programming"

| Folder | Content | Runs on |
|---|---|---|
| `pico-c/asm_sum` | C calls a function written in Thumb assembly (`sum_m0.S`), inline assembly | Pico in Wokwi (browser) |
| `pico-rust` | `asm_sum`: assembly with `global_asm!` and `asm!`; `button_lib`: uses the `debounce` library | Pico in Wokwi (VS Code) |
| `debounce` | hardware independent Rust library with unit tests (`cargo test`) | PC / Replit and any microcontroller |
| `c/register_struct.c` | register access with a struct overlay, bit fields | compile only |
| `micropython` | MicroPython: LED, button interrupt, ADC/PWM, `mem32` register access | Pico in Wokwi (browser, MicroPython project) |
| `python/decode_mpu6050.py` | Python 3 on the PC: binary data with `struct` | PC / Replit |

The Pico examples use the circuit of chapter 6 (`diagram.json`).

```sh
cd debounce && cargo test                       # unit tests on the PC
cd pico-rust && cargo build --release           # firmware for the Pico
python3 python/decode_mpu6050.py
```

## Tested

* `asm_sum` (C and Rust) in Wokwi: assembly and C/Rust both return 126541.
* `button_lib` in Wokwi: debouncing scenario passes 3 of 3 runs.
* `debounce`: 4 unit tests pass on the PC; the library also builds for `thumbv6m-none-eabi`.
* GDB session: `wokwi-cli -g 3333` + `arm-none-eabi-gdb` on `asm_sum` (see the chapter).
* `decode_mpu6050.py` runs with Python 3; `register_struct.c` compiles without warnings.
* The MicroPython scripts were only checked for syntax (not run in the simulator).
