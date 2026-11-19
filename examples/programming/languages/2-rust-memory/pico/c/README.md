# 2p · Memory safety: C on the Pico (PlatformIO)

| | |
|---|---|
| Board | **Raspberry Pi Pico** (RP2040, Cortex-M0+), `wokwi-pi-pico` in `diagram.json` |
| PlatformIO environment | **`pico`** (`board = rpipico`) |
| Build | PlatformIO check mark, or Run Task "2p: C - build for Pico" (`pio run`) |
| Firmware for Wokwi | `.pio/build/pico/firmware.uf2` (+ `.elf`) |
| Output | serial monitor (Serial1 on GP0/GP1, 115200 baud) |

## What the program does

A data logger keeps readings (in 0.1 degC) in a buffer that grows with `realloc()`.
It remembers a pointer `first` to the first reading. When the buffer grows it is moved and the old
block is freed; `malloc(8)` hands this block out again and writes "OK" into it.
The program then reads the first reading through the old pointer and decides about an alarm.

## Expected behaviour – the bug is the point of this example

```
first reading: 215 (address 0x20002320)
logger running, message at 0x20002330
buffer is now at        0x20002358
first reading: 19279   <- read through the old pointer (0x4B4F = "OK")
alarm (first reading > 30.0 degC): YES
```

The addresses can differ between builds. What matters:

* the buffer address changes (the buffer **was moved**),
* the second `first reading` is not 215 but 19279 = the bytes 'O' 'K',
* the alarm is raised although the temperature was 21.5 degC: a **false alarm**.

The compiler gives no warning and the program does not crash. This silent wrong value *is* the error
that the example demonstrates. Compare with the Rust version in `../rust`.

## Other observations

| You see | Meaning |
|---|---|
| second `first reading: 215`, alarm `no` | the block was not reused (e.g. `malloc(8)` removed, or the buffer could grow in place): the bug is still there, it is just not visible – typical for use-after-free |
| `panic: out of memory` | heap exhausted (only if you increase the loop a lot) |
| serial monitor stays empty | wrong board in `diagram.json` or firmware not built |
