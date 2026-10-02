# Embedded Computing

Lecture and lab material for Embedded Computing at RWU (Prof. Dr. Markus Pfeil,
with kind permission of Prof. Dr.-Ing. Franz Brümmer).

| Folder      | Content                                                  |
|-------------|----------------------------------------------------------|
| `pdf/`      | Script and slides, ready to read                         |
| `*.tex`     | LaTeX sources of script and slides (WS 2026/27)          |
| `examples/` | Runnable examples for each chapter, in C and Rust        |
| `Lab-2021/` | The earlier lab with the ET1 robot (see below)           |
| `archive/`  | Older scripts (2020), instruction set notes, print orders |

## Script and slides

- [Script (A4)](pdf/EmbeddedComputing_Script.pdf)
- [Slides (A5 landscape)](pdf/EmbeddedComputing_Slides.pdf)

## Build

```
make            builds docu.pdf (script) and slides.pdf (slides)
make script     only the script
make slides     only the slides
make publish    builds both and copies them into pdf/
make clean      removes LaTeX build artifacts
```

Requires TeX Live with latexmk and pdflatex.

## Structure

```
docu.tex (script, A4)        slides.tex (slides, A5 landscape)
      \                        /
       +---- preamble.tex ----+      common packages, listings setup
       +---- mathmacros.tex --+      macros (\bi, \ite, \defn, \qbox, ...)
       |                      +--    mathmacros-sl.tex (slide overrides)
       +---- text.tex --------+      list of chapters
                |
 Intro, Modelling, Cyber_Physical_Systems, Processors, Programming,
 Interfaces, Networking, OperatingSystems   (*.tex)
```

Script vs. slides:

- `\nsl{...}`: text only in the script
- `\os{...}`: text only on the slides (typically `\os{\newpage}` = slide break)

Figures live in `figures/`. Literature is in `refs.bib`; all entries are listed
in script and slides. All sources are UTF-8 with LF line endings.

## Examples

Each folder in `examples/` has its own README.md with instructions.

| Folder         | Ch. | Content                                                        |
|----------------|-----|----------------------------------------------------------------|
| `modelling/`   | 2   | Coffee machine FSM, C and Rust (Pico)                          |
| `cps/`         | 3   | Modelica models, Python simulation (plots of ch. 3)            |
| `processors/`  | 4   | One C function compiled for AVR, Cortex-M0+/M4, RISC-V         |
| `programming/` | 5   | Assembly from C and Rust, Rust library with tests, MicroPython |
| `interfaces/`  | 6   | GPIO, IRQ, PWM, ADC, UART, I2C, SPI, watchdog (Pico)           |
| `networking/`  | 7   | Wi-Fi, HTTP, NTP, MQTT (ESP32-C3), sockets on the PC           |
| `os/`          | 8   | FreeRTOS and Embassy tasks, queues, mutex (ESP32-C3)           |
| `linux/`       | 5/8 | Yocto image in QEMU, SDK cross-compiling, remote debugging     |
| `jslinux/`     | 5/8 | Small C programs to build and debug in Linux in the browser    |

C examples run in the browser on <https://wokwi.com>. Rust examples are built
with cargo and simulated with the Wokwi extension for VS Code. The
`.devcontainer` sets up a GitHub Codespace for the Linux exercises.

## Lab 2021: ET1 robot

The earlier lab used the ET1 robot, a Raspberry Pi on a motor board. Task
descriptions and solutions are in `Lab-2021/Tasks/`; board schematics, layout
and data sheets are in `Lab-2021/`.

Prerequisites for working with the robot:

- ET1 hardware, Micro USB charger (phone charger)
- Basic knowledge of remote access over a wireless access point (WLAN AP)

**Important:** before powering the ET1, position it so that it cannot fall off
should it start to move.

Preparation:

- Install the VNC Viewer: <https://www.realvnc.com/en/connect/download/viewer/raspberrypi/>
- Guides for the access point WLAN connection:
  <https://www.bitblokes.de/raspap-raspberry-pi-als-hotspot-access-point-wlan-wi-fi-benutzen>,
  <https://raspap.com>

Startup:

Prepare the ET1 by either connecting the Raspberry Pi to a USB power supply
directly on the Raspi board (as shown at the handover) or by charging the 9V
battery using the Micro USB charging port and powering the Raspberry Pi on using
the switches on the ET1. The switch close to the USB ports at the rear end of the
board switches the battery system on, powering the motors. To power the
Raspberry Pi from the battery you need to set the second switch close to the front
to the ON position (labelled on the board).

Powering the Raspberry Pi from the battery is problematic because it will run
out suddenly and could lead to loss of unsaved work. However, if your power
supply does not deliver enough current, the network connection might be
unstable. If connecting through the wireless is not stable, consider running
it from the battery instead.

1. Power the Raspberry Pi on and wait until the wireless access point comes
   up. This might take a few minutes. Connect your wireless adapter to the ET1
   using the WLAN AP.
   - SSID: `raspi-webgui`, password: `ChangeMe`
   - IP address of the hotspot: `10.3.141.1`
   - WebGUI (administration): `10.3.141.1`, user `admin`, password `secret`
2. Using the VNC Viewer, connect to the Raspberry Pi and access the desktop.
3. Verify the image has the necessary programs: Thonny (Python IDE), a C IDE,
   node.js, Firefox.
