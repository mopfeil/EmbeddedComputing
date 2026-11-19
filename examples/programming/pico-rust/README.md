# Rust on the Pico: assembly and the debounce library (cargo, no PlatformIO)

| | |
|---|---|
| Board | Raspberry Pi Pico (RP2040, Cortex-M0+), the circuit of chapter 6 (`diagram.json`) |
| PlatformIO environment | **none** – built with cargo (`rustup target add thumbv6m-none-eabi` once) |
| Build | `cargo build --release` (builds both programs in `src/bin/`) |
| Choose the program | set `firmware` and `elf` in `wokwi.toml` to `asm_sum` or `button_lib` |
| Run | F1 -> "Wokwi: Start Simulator"; for GDB "... and Wait for Debugger", then `arm-none-eabi-gdb` on port 3333 |
| Output | serial monitor (UART0 on GP0/GP1, 115200 baud) |

## `asm_sum`: a function in assembly, called from Rust

`asm_sum(a, n)` adds `n` unsigned 16 bit values and returns the 32 bit sum – the same as
`rust_sum()`. It is written in Thumb assembly with `global_asm!`; `asm!` reads the stack pointer and adds two registers.

Expected:

```
asm_sum  = 126541
rust_sum = 126541
sp = 0x2003ff98, 40 + 2 = 42
```

1 + 2 + 3 + 1000 + 60000 + 65535 = 126541. Both lines must be equal.

| You see | Cause (typical after a change of the assembly) |
|---|---|
| `asm_sum` differs from `rust_sum` | e.g. `ldrb` instead of `ldrh` (only the low byte of each value), or a signed load: 60000 and 65535 become negative and the sum is 126541 - 2 * 65536 = -4531 (printed as 4294962765) |
| `asm_sum = 0` | the loop is never entered: `ble` taken (n <= 0) or the result was not moved to `r0` |
| output stops, or random values after the call | the function changed `r4`–`r7` without `push`/`pop` (AAPCS: callee-saved), or `bx lr` is missing and the CPU runs into the next code |
| the Pico hangs right after `asm_sum` | HardFault: the Cortex-M0+ faults on unaligned accesses, e.g. `adds r0, r0, #1` instead of `#2` (unaligned `ldrh`) or `ldr` instead of `ldrh` (32 bit load from an address that is not a multiple of 4); `panic-halt` / the fault handler stop silently – check with GDB (`info registers`) |

## `button_lib`: the debounce library on the hardware

The button on GP14 toggles the LED on GP15. The same `debounce` crate is unit-tested on the PC (`cd ../debounce && cargo test`).

Expected: **one** toggle per click, even though the simulated button bounces. An error: the LED
toggles twice or not at all per click (threshold too small or `Edge::Released` used), or reacts
on release instead of press.
