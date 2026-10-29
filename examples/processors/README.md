# Examples for chapter "Processors"

`compile.sh` translates two small C files for several processors and keeps
the assembly listings. Without installing anything, the same comparison can
be done on <https://godbolt.org> (Compiler Explorer).

## sum.c: integer loop (`-Os`)

| file | processor | compiler used for the slides |
|---|---|---|
| `sum_avr.s` | ATmega328P (8 bit AVR, Arduino Uno) | avr-gcc 7.3.0 |
| `sum_m0.s` | ARM Cortex-M0+ (RP2040) | arm-none-eabi-gcc 16.1.0 |
| `sum_m4.s` | ARM Cortex-M4 (e.g. STM32F4) | arm-none-eabi-gcc 16.1.0 |
| `sum_rv.s` | RISC-V RV32IMC (ESP32-C3) | riscv32-esp-elf-gcc 14.2.0 |

Results: instructions in the loop body AVR 12, Cortex-M0+ 7,
Cortex-M4 6, RISC-V 7; code size 40, 24, 24 and 28 bytes.

## dot.c: Q15 and float dot product (`-O2` / `-O3`)

A typical signal processing kernel, once in fixed point (Q15) and once
in single precision float.

| file | processor | what to look for |
|---|---|---|
| `dot_m0.s` | Cortex-M0+ | `muls` + `adds`; float calls `__aeabi_fmul` / `__aeabi_fadd` (software) |
| `dot_m4.s` | Cortex-M4F | `smlabb` (16x16+32 MAC), `vfma.f32` (fused multiply-add in the FPU) |
| `dot_m55.s` | Cortex-M55 (Helium) | low-overhead loop `dls`/`le`; float vector loads, but sums added one by one |
| `dot_m55_fast.s` | Cortex-M55, `-ffast-math` | four float products and sums per iteration (`vmul.f32`/`vadd.f32 q`) |
| `dot_rv.s` | RISC-V RV32IMC (ESP32-C3) | `mul` + `add`; float calls `__mulsf3` / `__addsf3` |
| `dot_s3.s` | Xtensa LX7 (ESP32-S3) | zero-overhead `loop`, MAC16 `mula.aa.ll` into `ACCLO`, `madd.s`, register windows (`entry`/`retw`) |

Compilers: arm-none-eabi-gcc 16.1.0, riscv32-esp-elf-gcc 14.2.0,
xtensa-esp32s3-elf-gcc 14.2.0 (from the Arduino-Pico and Arduino-ESP32 cores).
