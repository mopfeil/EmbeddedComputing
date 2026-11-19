# 2p · Memory safety: Rust on the Pico (cargo, no PlatformIO)

| | |
|---|---|
| Board | **Raspberry Pi Pico** (RP2040, Cortex-M0+), `wokwi-pi-pico` in `diagram.json` |
| PlatformIO environment | **none** – this folder is built with cargo (`rustup target add thumbv6m-none-eabi` once) |
| Build | Run Task "2p: Rust - build the corrected firmware" (`cargo build --release`) |
| Show the compiler error | Run Task "2p: Rust - compile the dangling version (rejected)" (`cargo build --release --example dangling`) |
| Firmware for Wokwi | `target/thumbv6m-none-eabi/release/pico-memory` (ELF) |
| Output | serial monitor (UART0 on GP0/GP1, 115200 baud) |

## What the programs do

`examples/dangling.rs` is the C program of `../c` in Rust: a reference `first = &log[0]`, then
`log.push()` in a loop. `src/main.rs` is the corrected version: it copies the value
(`let first = log[0];`). Both use a 16 KB heap (`embedded-alloc`) for `Vec` and `String`.

## Expected behaviour

1. The dangling version **must not compile**. This is the expected result:

   ```
   error[E0502]: cannot borrow `log` as mutable because it is also borrowed as immutable
   ```

   rust-analyzer already underlines `log.push(220 + i)` while you type. There is no firmware for it.

2. The corrected firmware in Wokwi:

   ```
   first reading: 215 (buffer at 0x20000000)
   logger running, message at 0x20000008
   buffer is now at 0x20000108
   first reading: 215 (OK)
   alarm (first reading > 30.0 degC): no
   reading 500 does not exist (101 readings)
   ```

   The buffer moves as in C, but the copy stays 215: no false alarm. `log.get(500)` shows that
   an out of bounds access is caught too.

## What indicates an error

| You see | Cause |
|---|---|
| the dangling example **compiles** | it was changed (e.g. `let first = log[0];`): then it is the fixed version |
| ``error[E0463]: can't find crate for `core` `` | the target is missing: `rustup target add thumbv6m-none-eabi` |
| the simulation waits and prints nothing | started with "Wokwi: Start Simulator and Wait for Debugger" (`wokwi.toml` has `gdbServerPort = 3333`): connect GDB, or use "Wokwi: Start Simulator" |
| output stops in the middle, nothing else happens | panic: `panic-halt` stops silently (e.g. `log[500]` instead of `log.get(500)`); in GDB the PC is in `panic_halt` |
