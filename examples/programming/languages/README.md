# Three language experiments (chapter Programming, section "Programming Languages: Then and Now")

Open `languages.code-workspace` in VS Code. Each folder has its own tasks
(Terminal > Run Task) and debug configurations. Everything runs on the PC:
Linux, macOS, or Windows with WSL. You need `gcc`, `make`, Rust (`rustup`) and Python 3.

| Folder | Shows | Run |
|---|---|---|
| `1-inline-asm` | One line of inline assembly (CRC instruction) makes a CRC-32C checksum about 90x faster than the bitwise C version | `make run`, `make asm` |
| `2-rust-memory` | Dangling pointer after `realloc`: C prints a wrong value, AddressSanitizer finds it at run time, Rust rejects it at compile time | `make -C c run`, `make -C c asan`, `cargo run --example dangling` (fails on purpose), `cargo run` |
| `3-python` | Vibration analysis with an FFT in about 10 lines; the speed cost of Python loops | `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then `make_data.py`, `analyse.py`, `speed.py` |

## Tested (2026-11-05, AMD EPYC 9354P, gcc 15, Rust 1.99, Python 3.14)

* `crc32c`: bitwise 106 MB/s, table 455 MB/s (4.3x), inline asm 9.7 GB/s (91x). All three give the same CRC, and the self test ("123456789" -> 0xE3069283) passes.
* The AArch64 line (`crc32cx`) was checked with the LLVM assembler only. It has not been run on ARM hardware.
* `dangling.c`: prints 10968 instead of 215. The ASan build reports `heap-use-after-free` at line 47. `cargo run --example dangling` fails with E0502, and `cargo run` prints 215.
* `analyse.py` finds 24.5 Hz, 50 Hz and 137 Hz. `speed.py`: Python loop 20 ms, `sum()` 3.5 ms, NumPy 0.9 ms. The same loop in C (`gcc -O2`) takes 0.14 ms.
