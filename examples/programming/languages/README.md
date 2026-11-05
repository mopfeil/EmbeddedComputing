# Three language experiments (chapter Programming, section "Programming Languages: Then and Now")

Open `languages.code-workspace` in VS Code. Each folder has its own tasks
(Terminal > Run Task) and debug configurations. The folders 1-3 run on the PC:
Linux, macOS, or Windows with WSL. You need `gcc`, `make`, Rust (`rustup`) and Python 3.
The folders 1p-3p are the same experiments on the Raspberry Pi Pico in the
Wokwi simulator (VS Code extension "Wokwi Simulator"): build with the task,
then F1 > "Wokwi: Start Simulator".

| Folder | Shows | Run |
|---|---|---|
| `1-inline-asm` | One line of inline assembly (CRC instruction) makes a CRC-32C checksum about 90x faster than the bitwise C version | `make run`, `make asm` |
| `2-rust-memory` | Dangling pointer after `realloc`: C prints a wrong value, AddressSanitizer finds it at run time, Rust rejects it at compile time | `make -C c run`, `make -C c asan`, `cargo run --example dangling` (fails on purpose), `cargo run` |
| `3-python` | Vibration analysis with an FFT in about 10 lines; the speed cost of Python loops | `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then `make_data.py`, `analyse.py`, `speed.py` |

## On the Pico in Wokwi

| Folder | Board | Shows | Build |
|---|---|---|---|
| `1-inline-asm/pico` | Pico 2 (RP2350, Cortex-M33) | FIR filter: one `smlad` instruction (2 multiply-accumulates) instead of the C loop: 1.9x faster | `arduino-cli compile -b rp2040:rp2040:rpipico2 --output-dir build fir_smlad` |
| `2-rust-memory/pico/c` | Pico (RP2040) | the dangling pointer reads the text "OK" from a reused block as 19279 = 1927.9 degC: **false alarm** | `arduino-cli compile -b rp2040:rp2040:rpipico --output-dir build dangling` |
| `2-rust-memory/pico/rust` | Pico (RP2040) | the same in Rust with a heap (`embedded-alloc`): rejected (E0502); corrected version prints no alarm | `cargo build --release` / `cargo build --release --example dangling` |
| `3-python/pico` | Pico (RP2040), MicroPython 1.29 | DFT spectrum in a few lines on the MCU; price of the interpreter, `@micropython.native` and `@viper` | `python make_uf2.py` (MicroPython + file system with `main.py` in one `.uf2`) |

Setup for the Arduino examples (once):

```sh
arduino-cli core install rp2040:rp2040 --additional-urls https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
rustup target add thumbv6m-none-eabi          # for the Rust example
```

Without VS Code, all of them also run on https://wokwi.com: paste the `.ino` into a new
Pico (or Pico 2) Arduino project, or `main.py` into a new MicroPython Pico project.
The C reference for the MicroPython speed test is in `3-python/pico/c_reference`
(in VS Code: F1 > "Wokwi: Select Config File").

## Tested (2026-11-05, AMD EPYC 9354P, gcc 15, Rust 1.99, Python 3.14)

* `crc32c`: bitwise 106 MB/s, table 455 MB/s (4.3x), inline asm 9.7 GB/s (91x). All three give the same CRC, and the self test ("123456789" -> 0xE3069283) passes.
* The AArch64 line (`crc32cx`) was checked with the LLVM assembler only. It has not been run on ARM hardware.
* `dangling.c`: prints 10968 instead of 215. The ASan build reports `heap-use-after-free` at line 47. `cargo run --example dangling` fails with E0502, and `cargo run` prints 215.
* `analyse.py` finds 24.5 Hz, 50 Hz and 137 Hz. `speed.py`: Python loop 20 ms, `sum()` 3.5 ms, NumPy 0.9 ms. The same loop in C (`gcc -O2`) takes 0.14 ms.
* Pico 2 / Wokwi (simulated time, 150 MHz): FIR with 32 taps over 1024 samples. C takes 3278 us and `smlad` takes 1735 us (1.9x), with identical results. The compiler uses `smlabb` (one multiply-accumulate) for the C loop.
* Pico / Wokwi, C: the first reading is printed as 19279 (0x4B4F = "OK"), so the alarm is wrongly raised. Rust: `--example dangling` fails with E0502. The corrected firmware prints 215 and no alarm.
* Pico / Wokwi, MicroPython 1.29: all variants find 24, 50 and 138 Hz. `spectrum()` (comprehension with `exp`) takes 14.4 s and `dft_loop` 1.9 s. Mean of 10000 values: Python loop 39.6 ms, `sum()` 24.4 ms, `@native` 25.8 ms, `@viper` 3.8 ms; C (`c_reference`, -Os, built for 125 MHz like MicroPython) takes 0.65 ms. Wokwi reports the same 0.65 ms for a 200 MHz build, so the simulated RP2040 apparently does not speed up with the clock setting.
* Checked only with wokwi-cli, not inside the VS Code extension: the `rfc2217ServerPort`/mpremote route and the Wokwi web projects.
