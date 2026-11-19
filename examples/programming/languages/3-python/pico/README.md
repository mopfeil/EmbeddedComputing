# 3p · MicroPython on the Pico (no PlatformIO)

| | |
|---|---|
| Board | **Raspberry Pi Pico** (RP2040), `wokwi-pi-pico` in `diagram.json`, **no** serial monitor connection on GP0/GP1 |
| PlatformIO environment | **none** – the firmware is the official MicroPython 1.29 image plus a file system with `main.py` |
| Set-up (once) | Run Task "3p: set up .venv (once)" – creates `../.venv` with `littlefs-python` and `mpremote` |
| Build | Run Task "3p: build main.uf2 (MicroPython + main.py)" (`python make_uf2.py`) – after **every** change of `main.py` |
| Firmware for Wokwi | `build/main.uf2` |
| Output | serial monitor of the simulator (MicroPython prints on USB) |
| C reference | `c_reference/`: PlatformIO environment **`pico`** (`board = rpipico`, 125 MHz like MicroPython) |

## What the program does

`main.py` creates 500 simulated acceleration samples (24 Hz imbalance, 50 Hz mains hum, 138 Hz
bearing damage, noise), computes the spectrum 0–200 Hz twice (`spectrum()`: one expression with
`cmath.exp`; `dft_loop()`: loops with a rotating phasor) and prints the three strongest peaks.
Then it measures four ways to compute the mean of 10000 ADC values.

## Expected behaviour

The simulation is slower than real time: the first lines appear after some seconds, the DFT lines
need 14 s and 2 s of *simulated* time, which can take a few minutes on the PC. Be patient.

```
CPU clock 125 MHz
spectrum 0..200 Hz of 500 samples:
spectrum      14453 ms   24 Hz: 0.31 g, 50 Hz: 0.09 g, 138 Hz: 0.07 g
dft_loop       1874 ms   24 Hz: 0.31 g, 50 Hz: 0.09 g, 138 Hz: 0.07 g
mean of 10000 ADC values:
  Python loop    39617 us   mean = 2042
  sum()          24380 us   mean = 2042
  @native        25818 us   mean = 2042
  @viper          3823 us   mean = 2042
MicroPython v1.29.0 on 2026-08-24; Raspberry Pi Pico with RP2040
Type "help()" for more information.
>>>
```

At the end `main.py` is finished and the interactive prompt `>>>` appears: this is normal.

Correct: both DFT versions find **24, 50 and 138 Hz**, all four means are equal, `@viper` is about
ten times faster than the Python loop. The C reference (`c_reference`) prints about 650 us.

## What indicates an error

| You see | Cause |
|---|---|
| serial monitor stays empty | `main.uf2` not built (only the MicroPython image), or GP0/GP1 connected to the serial monitor in `diagram.json` – the REPL is on USB |
| only the `>>>` prompt, no result lines | `main.py` is not in the file system: run the build task again |
| your change of `main.py` has no effect | the `.uf2` contains the old `main.py`: rebuild, or use the task "run main.py in the running simulation (mpremote)" |
| `MemoryError` | big buffers allocated after the DFT (heap fragmented) – allocate them first, as `main.py` does |
| `ViperTypeError` or `NameError: ptr16` | `ptr16` exists only inside a function with `@micropython.viper` |
| the means differ | an error in one of the variants (e.g. `s // n` with the wrong `n`) |
| `make_uf2.py`: `No module named littlefs` | the `.venv` was not set up |
