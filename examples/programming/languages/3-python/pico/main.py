"""What Python makes easy - on the Raspberry Pi Pico with MicroPython.

The vibration analysis of ../analyse.py, now on the microcontroller itself:
500 acceleration samples at 1 kHz (simulated here, as from an MPU-6050),
a spectrum computed with complex numbers, the three strongest frequencies.
There is no NumPy on the Pico, but the discrete Fourier transform (DFT)
still takes only a few lines of Python: see spectrum().

And the price: the interpreter is slow. How a loop is written matters a
lot, and for integer loops the decorators micropython.native and
micropython.viper compile a function to machine code - like NumPy on the
PC, the fix is to leave the interpreter for the inner loop.

Wokwi: new MicroPython project for the Pico, paste this file as main.py.
VS Code: see ../README.md (Wokwi + mpremote).
"""
import array
import cmath
import math
import random
import time

import machine
import micropython

FS = 1000                         # sample rate in Hz
N = 500                           # samples -> 2 Hz frequency resolution

# 10000 ADC values (12 bit) for the speed test at the end. Allocated first:
# later the heap is fragmented by the many small objects of the DFT.
adc = array.array("H", bytearray(2 * 10000))   # MicroPython: raw bytes -> 10000 zeros
for i in range(len(adc)):
    adc[i] = (i * 37) & 0xFFF

# simulated sensor log: imbalance 24 Hz, mains hum 50 Hz, bearing 138 Hz
random.seed(1)
a = [0.30 * math.sin(2 * math.pi * 24 * n / FS)
     + 0.10 * math.sin(2 * math.pi * 50 * n / FS)
     + 0.06 * math.sin(2 * math.pi * 138 * n / FS)
     + (random.random() - 0.5) * 0.5 for n in range(N)]


def spectrum(x, fmax):
    """Amplitude for every 2 Hz bin from 0 to fmax: the DFT in one expression."""
    w = -2j * cmath.pi / len(x)
    return [abs(sum(v * cmath.exp(w * k * n) for n, v in enumerate(x))) * 2 / len(x)
            for k in range(fmax * len(x) // FS)]


def dft_loop(x, fmax):
    """The same with plain loops; a rotating phasor replaces exp()."""
    w = -2j * cmath.pi / len(x)
    out = []
    for k in range(fmax * len(x) // FS):
        s = 0j
        step = cmath.exp(w * k)
        r = 1 + 0j
        for v in x:
            s += v * r
            r *= step
        out.append(abs(s) * 2 / len(x))
    return out


print(f"CPU clock {machine.freq() // 1000000} MHz")
print("spectrum 0..200 Hz of 500 samples:")
for name, f in (("spectrum", spectrum), ("dft_loop", dft_loop)):
    t0 = time.ticks_ms()
    amp = f(a, 200)               # 0 .. 200 Hz
    dt = time.ticks_diff(time.ticks_ms(), t0)
    top = sorted(range(len(amp)), key=lambda k: amp[k])[-3:]
    peaks = ", ".join(f"{k * FS // N} Hz: {amp[k]:.2f} g" for k in reversed(top))
    print(f"{name:12s} {dt:6d} ms   {peaks}")


# The price: the mean of 10000 ADC values (12 bit), four ways


def mean_loop(d):
    s = 0
    for v in d:
        s += v
    return s // len(d)


@micropython.native
def mean_native(d):
    s = 0
    for v in d:
        s += v
    return s // len(d)


@micropython.viper
def mean_viper(d, n: int) -> int:
    p = ptr16(d)                  # raw pointer to the 16 bit values
    s = 0
    for i in range(n):
        s += p[i]
    return s // n


print("mean of 10000 ADC values:")
for name, f in (("Python loop", lambda: mean_loop(adc)), ("sum()", lambda: sum(adc) // len(adc)),
                ("@native", lambda: mean_native(adc)), ("@viper", lambda: mean_viper(adc, len(adc)))):
    t0 = time.ticks_us()
    m = f()
    dt = time.ticks_diff(time.ticks_us(), t0)
    print(f"  {name:12s} {dt:7d} us   mean = {m}")
