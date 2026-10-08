# Climate chamber: a controller and its simulated environment

Case study for the chapter "Operating Systems" (section "Case Study"). An
ESP32-C3 with FreeRTOS holds a small chamber at 40 °C. The chamber and its
fan are **custom chips**: small C programs that Wokwi runs next to the
processor and that model the physics. The program knows them only through
its interfaces, exactly as it would know real hardware.

```
 ESP32-C3 + FreeRTOS                          environment model (custom chips)
 ┌──────────────────────┐   I2C 0x48 (8/9)   ┌──────────────────────────────┐
 │ sensor  (3) 100 ms ──┼────────────────────┼─ plant: TMP102-like sensor   │
 │   │ queue            │   PWM heater (6)   │  tau dT/dt = Kh d            │
 │ control (4) PI ──────┼───────────────────►│    - (1 + ka a)(T - Ta)      │
 │   ▲ event group      │   PWM fan (7)      │         ▲ AIR (analog)       │
 │ fan     (2) rpm ─────┼───────────────────►│ fan: rotor tau = 0.5 s       │
 │   ▲ ISR ◄────────────┼── TACH (5) ────────┼─ 2 pulses / revolution       │
 │ display (1) LCD 0x27 │                    └──────────────────────────────┘
 └──────────────────────┘   + alarm LED (10), logic analyzer on all signals
```

| File | Content |
|---|---|
| `chamber.ino` | the program: 4 tasks, queue, mailbox, mutex, event group, ISR |
| `chips/plant.chip.{c,json}` | thermal model, TMP102 register set on I2C, controls "ambient" and "sensor fault" |
| `chips/fan.chip.{c,json}` | fan with rotor inertia, tachometer and airflow output, control "rotor blocked" |
| `diagram.json`, `libraries.txt` | circuit (incl. LCD 1602 I2C and logic analyzer), library list |
| `wokwi.toml` | for Wokwi for VS Code and `wokwi-cli` |
| `test/faults.yaml` | scenario: blocks the fan at 20 s, silences the sensor at 38 s |
| `test/figures.py` | creates the figures of the lecture from the simulator output |

## Run in the browser

Open a new ESP32-C3 project on <https://wokwi.com/projects/new/esp32-c3>,
replace `sketch.ino` and `diagram.json`, add `libraries.txt`, and create the
two custom chips (file menu "New file…" → "Custom chip (C)") named `plant`
and `fan`, then paste the content of the four files from `chips/`. Wokwi
compiles the chips in the browser.

During the simulation, click on a chip to change its controls: ambient
temperature, sensor fault, rotor blocked. The logic analyzer records a VCD
file when the simulation stops (open it with PulseView, I2C decoder on D0/D1).

## Run locally

```sh
arduino-cli compile -b esp32:esp32:esp32c3 --output-dir build .
wokwi-cli chip compile chips/plant.chip.c -o chips/plant.chip.wasm
wokwi-cli chip compile chips/fan.chip.c -o chips/fan.chip.wasm
wokwi-cli --timeout 30000 .                                    # needs WOKWI_CLI_TOKEN
wokwi-cli --scenario test/faults.yaml --serial-log-file good.csv . > good.log
wokwi-cli --timeout 20500 --vcd-file la.vcd .
```

Needs the ESP32 core and the library "LiquidCrystal I2C"
(`arduino-cli lib install "LiquidCrystal I2C"`). The first `chip compile`
downloads the WASI SDK and `wokwi-api.h`.

The serial output is CSV: `t_ms,temp,heat,fan,rpm,faults` (faults: bit 0 fan
stalled, bit 1 sensor lost). The plant chip prints the true temperature every
500 ms (`[chip-plant] plant ... T=...`), so the simulation shows what the
program measures and what really happens.

## Tested

With `wokwi-cli` 0.28.1 and arduino-esp32 in October 2026:

| Test | Result in the simulator |
|---|---|
| start, ambient 20 °C | 40.00 °C after about 17 s, heater 53 %, fan 40 % = 1200 rpm |
| logic analyzer | temperature read every 100.0 ms (0.5 ms at 100 kHz: `S 90 00 S 91 28 00 P`); LCD update 95 ms every 500 ms |
| fan blocked at 21.3 s | alarm at 23.3 s (2.0 s), heater off; cleared 0.5 s after the fan turns again |
| sensor silent at 39.3 s | alarm at 39.8 s (queue timeout 0.5 s), heater off; the chamber cools to 27 °C |
| same, without the return value check | program reads 0xFFFF = −0.06 °C, heater 100 %, chamber 49 °C while the log shows −0.06 °C |

Not tested: the small temperature bar on the plant chip (`wokwi-cli` cannot
take a screenshot of a custom chip).
