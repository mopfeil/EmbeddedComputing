# GPIO output stages in Falstad CircuitJS

Circuits for the worksheet *GPIO Output Stages in Simulation*
(`Worksheet_IO_Ports.tex` in the lecture folder). They run in the browser
simulator [Falstad CircuitJS](https://www.falstad.com/circuit/): open the
worksheet PDF and click the link of a part, or load a file here with
*File → Open File*.

| File | Topic |
|---|---|
| `A_pushpull_characteristic.txt` | Push-pull output as a curve tracer: V_OH/V_OL over current, body diodes |
| `B_pushpull_capacitive_load.txt` | Rise/fall time with load capacitance, dynamic power, shoot-through |
| `C_bus_contention.txt` | Two push-pull outputs driving against each other |
| `D_open_drain_bus.txt` | I2C-like open-drain bus, pull-up sizing, wired AND, comparison with push-pull |
| `E_open_drain_overvoltage.txt` | Pull-up to 5 V: injection current, back-powering, 5 V-tolerant pins |
| `F_open_collector_inductive.txt` | NPN open collector with relay coil or lamp: kick-back, flyback diode, Zener, saturation |
| `G_transmission_line.txt` | Fast edges on a 50 Ohm trace: ringing, ESD diodes, series termination, slew rate |

All MOSFETs use the same square-law model: V_T = 0.6 V, beta_N = 12 mA/V²,
beta_P = 8 mA/V², supply 3.3 V. This matches roughly the 12 mA drive setting
of an RP2040 GPIO (V_OH = 2.62 V at 12.8 mA, V_OL = 0.4 V at 12 mA). Part G
uses the fastest drive setting (beta_N = 30 mA/V², beta_P = 25 mA/V²).

## Regenerating

The circuit files are generated; edit `make_circuits.py`, not the `.txt` files.

```sh
pip install lzstring
python3 make_circuits.py          # circuits + ../../../figures/falstad/links.tex
```

`check_circuits.py` runs every circuit headless on falstad.com (Playwright +
Chromium), prints the values used in the solutions and exports the schematics
for the worksheet:

```sh
pip install playwright lzstring numpy && playwright install chromium
python3 check_circuits.py           # all checks
python3 check_circuits.py B D       # only some parts
python3 check_circuits.py figures   # schematics -> figures/falstad/*_schematic.pdf
```

Then build the worksheet in the lecture folder with `make worksheet`.
