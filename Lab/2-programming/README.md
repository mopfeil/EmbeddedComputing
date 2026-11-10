# Lab task 2: programming the ET1 robot

You program the ET1 robot from the old lab: a START button, a red LED and two DC motors
behind an H-bridge. The robot runs as a model in the Wokwi simulator, so you need no hardware. A Raspberry Pi
Pico controls it, and you can choose **C**, **MicroPython** or **Rust**. All three folders contain the same
frame: wiring, set-up and empty functions with `TODO` comments. Fill in the TODOs in the order of their numbers.

## Set-up (once)

1. VS Code with the extension **Wokwi Simulator** (free licence: F1 > "Wokwi: Request a New License").
   Open `et1.code-workspace` (File > Open Workspace from File). VS Code offers the other extensions it recommends.
2. Install the tools for your language:

| Language | Needs | Build (Terminal > Run Build Task) | Firmware for Wokwi |
|---|---|---|---|
| C | extension **PlatformIO IDE** (the first build downloads the Pico core, a few minutes) | `pio run` | `c/.pio/build/pico/firmware.uf2` |
| MicroPython | Python 3; run the task "Python: set up .venv (once)" | `python make_uf2.py` (MicroPython + your `main.py` in one `.uf2`) | `python/build/main.uf2` |
| Rust | `rustup target add thumbv6m-none-eabi`, extension rust-analyzer | `cargo build --release` | `rust/target/thumbv6m-none-eabi/release/et1` |

3. Build, open a file of the same folder, then F1 > **"Wokwi: Start Simulator"**. Your `printf`/`print`/`writeln!`
   output appears in the serial monitor. Messages of the robot ("ET1 stopped at ...") appear there as well.

Each time you change the code: build again, then restart the simulator.
MicroPython has a faster route: while the simulation runs, the task "Python: run main.py in the running
simulation (mpremote)" sends `main.py` to it directly.

## The simulated hardware

| Pico pin | Connected to | |
|---|---|---|
| GP7 | red LED (via 330 Ω) | high = on |
| GP5 | START button to GND | internal pull-up: low = pressed |
| GP18 / GP17 / GP16 | ENA / IN1 / IN2 | left motor: PWM speed, direction |
| GP19 / GP20 / GP21 | ENB / IN3 / IN4 | right motor: PWM speed, direction |
| GP0 / GP1 | serial monitor (C, Rust) | MicroPython uses USB |

The H-bridge: `IN1 IN2 = 1 0` forward, `0 1` backward, `0 0` brake. The speed is the PWM duty cycle on ENA
(IN3/IN4/ENB the same for the right motor). Up to 12 % duty cycle a motor does not turn. Top speed is
0.25 m/s, and the wheels are 14 cm apart.

The **ET1 chip** shows a 2 m × 2 m floor from above, with grid lines every 0.5 m, the robot (blue, the white line points
forward) and its track. It starts in the centre, facing up. Top lines: `X`, `Y` position in m, `H` heading in
degrees (+ = turned left), `D` distance from the start point, `L`, `R` wheel speeds in %. Click the chip for
its control "Left motor weaker by (%)".

## Tasks

Set `TASK` at the top of the file to the task you are working on.

| Task | Function(s) | What to program |
|---|---|---|
| 1 | `motor(side, speed)`, `stop()` | Motor driver: speed −100 … +100 % → direction pins and PWM. You test it in tasks 3 and 4. |
| 2 | `button_clicked()`, `task2()` | Edge detection with 30 ms debouncing; each click toggles the LED and prints "LED on"/"LED off". |
| 3 | `task3()` | On a click: only the left wheel drives at 50 % for 10 s, then only the right wheel for 10 s, then stop. LED on while driving; print the time the sequence took. |
| 4 | `ramp(dir)`, `task4()` | Accelerate 10 … 80 % in steps of 0.5 s, brake back down to 0, then do the same backwards. Then compensate a weaker left motor with a trim factor (4c). |
| 5 | `wait_ms(ms)` | Emergency stop: every wait polls the button. A click while the robot drives stops it at once and ends the sequence. |

How to check your result:

* Task 2: holding the button down toggles the LED only once.
* Task 3: the track shows two circles around the wheels and takes 20 s.
* Task 4: ET1 ends where it started, so `D` shows almost 0.00. With "Left motor weaker by" set to 10 %, your trim keeps
  `H` within ±5° at the far end.
* Task 5: a click in the middle of the drive stops ET1, prints "EMERGENCY STOP" and ends the sequence. The
  next click starts it again.

## Files

| Path | Content |
|---|---|
| `c/src/main.cpp` | C frame (Arduino-Pico core, PlatformIO) |
| `python/main.py` | MicroPython frame; `make_uf2.py` builds the firmware |
| `rust/src/main.rs` | Rust frame; `rust/src/board.rs` holds the given hardware set-up |
| `*/diagram.json`, `*/wokwi.toml` | circuit and firmware path for Wokwi (the same circuit in all three folders) |
| `chip/` | the robot model as a Wokwi custom chip (`et1.chip.c`; given, already compiled to `et1.chip.wasm`) |

To change the robot model, compile it again with `wokwi-cli chip compile chip/et1.chip.c -o chip/et1.chip.wasm`.
