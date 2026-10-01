# Example for chapter "Processors"

`sum.c` contains one small C function. `compile.sh` translates it for

| file | processor | compiler used for the slides |
|---|---|---|
| `sum_avr.s` | ATmega328P (8 bit AVR, Arduino Uno) | avr-gcc 7.3.0 |
| `sum_m0.s` | ARM Cortex-M0+ (RP2040) | arm-none-eabi-gcc 16.1.0 |
| `sum_m4.s` | ARM Cortex-M4 (e.g. STM32F4) | arm-none-eabi-gcc 16.1.0 |
| `sum_rv.s` | RISC-V RV32IMC (ESP32-C3) | riscv32-esp-elf-gcc 14.2.0 |

All with `-Os`. Results: instructions in the loop body AVR 12, Cortex-M0+ 7,
Cortex-M4 6, RISC-V 7; code size 40, 24, 24 and 28 bytes.

Without installing anything, the same comparison can be done on
<https://godbolt.org> (Compiler Explorer).
