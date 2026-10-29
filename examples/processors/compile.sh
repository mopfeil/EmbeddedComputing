#!/bin/sh
# Compile sum.c and dot.c for several processors and keep the assembly listings.
# The compilers come with the Arduino cores (Arduino AVR, Arduino-Pico,
# Arduino-ESP32) - or install avr-gcc, arm-none-eabi-gcc and a RISC-V gcc.
# Alternative without installation: https://godbolt.org (Compiler Explorer).
set -e
# sum.c: integer loop, optimised for size
avr-gcc             -mmcu=atmega328p          -Os -S -o sum_avr.s  sum.c
arm-none-eabi-gcc   -mcpu=cortex-m0plus -mthumb -Os -S -o sum_m0.s sum.c
arm-none-eabi-gcc   -mcpu=cortex-m4     -mthumb -Os -S -o sum_m4.s sum.c
riscv32-esp-elf-gcc -march=rv32imc -mabi=ilp32 -Os -S -o sum_rv.s  sum.c
# dot.c: Q15 and float dot product (DSP kernel), optimised for speed
arm-none-eabi-gcc   -mcpu=cortex-m0plus -mthumb -O2 -S -o dot_m0.s dot.c
arm-none-eabi-gcc   -mcpu=cortex-m4 -mthumb -mfloat-abi=hard -mfpu=fpv4-sp-d16 -O2 -S -o dot_m4.s dot.c
arm-none-eabi-gcc   -mcpu=cortex-m55 -mthumb -mfloat-abi=hard -O3 -S -o dot_m55.s dot.c
arm-none-eabi-gcc   -mcpu=cortex-m55 -mthumb -mfloat-abi=hard -O3 -ffast-math -S -o dot_m55_fast.s dot.c
riscv32-esp-elf-gcc -march=rv32imc -mabi=ilp32 -O2 -S -o dot_rv.s dot.c
xtensa-esp32s3-elf-gcc -O2 -S -o dot_s3.s dot.c
