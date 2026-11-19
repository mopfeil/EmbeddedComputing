# 3p · C reference for the MicroPython speed test (PlatformIO)

| | |
|---|---|
| Board | Raspberry Pi Pico (RP2040), `wokwi-pi-pico` |
| PlatformIO environment | **`pico`** (`board = rpipico`, `board_build.f_cpu = 125000000L` like MicroPython) |
| Build | Run Task "3p: C reference - build for Pico (125 MHz)" (`pio run`) |
| Firmware for Wokwi | `.pio/build/pico/firmware.uf2` |

Expected output (Serial1, GP0/GP1):

```
CPU clock 125 MHz
  C (-Os)          644 us   mean = 2042
```

`mean = 2042` must be the same as in `../main.py`. A different clock (e.g. 133 MHz) means the
`f_cpu` line is missing. Note: the simulated RP2040 gives the same time at 200 MHz – Wokwi does not
follow the clock setting.
