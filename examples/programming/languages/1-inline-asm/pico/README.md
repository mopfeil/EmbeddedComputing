# 1p · Inline assembly on the Pico 2 (C, PlatformIO)

| | |
|---|---|
| Board | **Raspberry Pi Pico 2** (RP2350, Cortex-M33), `board-pi-pico-2` in `diagram.json` |
| PlatformIO environment | **`pico2`** (`board = rpipico2`) – the only environment in `platformio.ini` |
| Build | PlatformIO check mark, or Run Task "1p: build for Pico 2" (`pio run`) |
| Firmware for Wokwi | `.pio/build/pico2/firmware.uf2` (+ `.elf`) |
| Output | serial monitor of the simulator (Serial1 on GP0/GP1, 115200 baud) |

## What the program does

An FIR filter (moving average, 32 taps) over 1024 audio samples, computed twice:
`dot_c()` in plain C and `dot_asm()` with the DSP instruction `smlad`
(two 16 bit multiply-accumulates in one instruction). It measures both and compares the results.

## Expected behaviour

```
FIR filter, 32 taps, 1024 samples, 150 MHz
C        3278 us per block
smlad    1735 us per block   1.9x faster
results identical
```

Then nothing more happens (`loop()` is empty). The times are simulated time and are the same on every PC.

## What indicates an error

| You see | Cause |
|---|---|
| build error `selected processor does not support 'smlad ...' in Thumb mode` | built for the RP2040 (`board = rpipico`): the Cortex-M0+ has no DSP instructions. Use the environment `pico2`. |
| `results DIFFERENT` | the assembly version computes something else. Example (tested): `"=r"(s)` instead of `"+r"(s)` compiles without a warning, but tells the compiler that `smlad` does not read `s` – the accumulator starts with a random register value. Also: an odd `TAPS` (the loop takes two values per step) |
| speed-up about 1.0x | the asm line was removed, or `dot_asm` calls the C loop |
| serial monitor stays empty | `diagram.json` has the RP2040 board (`wokwi-pi-pico`) – RP2350 firmware does not start there – or the firmware was not built |
| "firmware not found" when starting Wokwi | not built yet, or the environment name in `wokwi.toml` does not match `platformio.ini` |
