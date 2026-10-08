#!/bin/sh
# Compile sum.c for four processors and keep the assembly listings.
# The compilers come with the Arduino cores (Arduino AVR, Arduino-Pico,
# Arduino-ESP32) - or install avr-gcc, arm-none-eabi-gcc and a RISC-V gcc.
# Alternative without installation: https://godbolt.org (Compiler Explorer).
set -e
avr-gcc             -mmcu=atmega328p          -Os -S -o sum_avr.s  sum.c
arm-none-eabi-gcc   -mcpu=cortex-m0plus -mthumb -Os -S -o sum_m0.s sum.c
arm-none-eabi-gcc   -mcpu=cortex-m4     -mthumb -Os -S -o sum_m4.s sum.c
riscv32-esp-elf-gcc -march=rv32imc -mabi=ilp32 -Os -S -o sum_rv.s  sum.c
