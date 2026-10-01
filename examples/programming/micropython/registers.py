# Direct register access from MicroPython: the same SIO registers as in
# chapter 6, accessed through machine.mem32.
from machine import Pin, mem32
import time

SIO_BASE = 0xD0000000
GPIO_OUT_XOR = SIO_BASE + 0x01C

Pin(15, Pin.OUT)                # let MicroPython configure the pin (FUNCSEL = SIO)

for _ in range(10):
    mem32[GPIO_OUT_XOR] = 1 << 15   # toggle GP15
    time.sleep_ms(250)

print("CPUID (core number):", mem32[SIO_BASE + 0x000])
