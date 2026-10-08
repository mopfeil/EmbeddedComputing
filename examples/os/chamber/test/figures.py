#!/usr/bin/env python3
"""Figures for the lecture from wokwi-cli output.

Expects in <datadir>:
  good.log, good.csv   wokwi-cli --scenario test/faults.yaml --serial-log-file good.csv . > good.log
  bad.log, bad.csv     the same with the return value check removed in readTemperature()
  la.vcd               wokwi-cli --timeout 20500 --vcd-file la.vcd .  (logic analyzer)
The .log files hold the ground truth printed by the plant chip, the .csv files
the serial output of the program.

usage: figures.py <datadir> <outdir>
"""
import re
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path

VIOLET, CYAN, RED, GRAY = "#6638b6", "#00a9ce", "#c0392b", "#888888"
FONTS = Path(__file__).resolve().parents[4] / "fonts"
for f in FONTS.glob("BarlowSemiCondensed-*.otf"):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({"font.family": "Barlow Semi Condensed", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})

HEADER_S = 1.27                      # the scenario starts its delays here
FAN_FAULT = (HEADER_S + 20, HEADER_S + 30)
SENSOR_FAULT = (HEADER_S + 38, HEADER_S + 44)


def read_log(prefix):
    """Returns (program rows, plant rows) as lists of tuples in seconds."""
    prog, plant = [], []
    for line in open(f"{prefix}.log", errors="replace"):
        m = re.match(r"\[chip-plant\] plant (\d+) ms: T=([-\d.]+) heat=([\d.]+) air=([\d.]+)", line)
        if m:
            plant.append((int(m[1]) / 1000, float(m[2]), float(m[3]), float(m[4])))
    for line in open(f"{prefix}.csv", errors="replace"):
        if re.match(r"^\d+,[-\d.]+,", line):
            t, temp, heat, fan, rpm, faults = line.strip().split(",")
            prog.append((int(t) / 1000, float(temp), float(heat), float(fan), int(rpm), int(faults)))
    return prog, plant


def shade(ax, labels=False, faults=((FAN_FAULT, "fan blocked"), (SENSOR_FAULT, "sensor fault"))):
    for (a, b), text in faults:
        ax.axvspan(a, b, color=RED, alpha=0.08, lw=0)
        if labels:
            ax.text((a + b) / 2, 1.02, text, transform=ax.get_xaxis_transform(),
                    ha="center", va="bottom", color=RED, fontsize=10)


def fig_faults(good, out):
    prog, plant = read_log(good)
    t = [r[0] for r in prog]
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(10, 5.2), sharex=True,
                                     gridspec_kw={"height_ratios": [2.2, 1, 1]})
    a1.plot([p[0] for p in plant], [p[1] for p in plant], color=CYAN, lw=3, alpha=0.5,
            label="true temperature\n(plant model)")
    a1.plot(t, [r[1] for r in prog], color=VIOLET, lw=1.4, label="what the program\nmeasures")
    a1.axhline(40, color=GRAY, lw=0.8, ls="--")
    a1.set_ylabel("°C")
    a1.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=10)
    a2.step(t, [r[2] * 100 for r in prog], where="post", color=RED, lw=1.2, label="heater")
    a2.step(t, [r[3] * 100 for r in prog], where="post", color=VIOLET, lw=1.2, label="fan demand")
    a2.set_ylabel("PWM %")
    a2.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=10)
    a3.plot(t, [r[4] for r in prog], color=CYAN, lw=1.4, label="fan speed\n(tachometer)")
    a3.step(t, [1500 * bool(r[5]) for r in prog], where="post", color=RED, lw=1, ls=":",
            label="fault flag")
    a3.set_ylabel("rpm")
    a3.set_xlabel("simulated time [s]")
    a3.legend(loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=10)
    for ax in (a1, a2, a3):
        shade(ax, labels=ax is a1)
    a3.set_xlim(0, t[-1])
    fig.align_ylabels()
    fig.tight_layout()
    fig.savefig(out)


def fig_nocheck(good, bad, out):
    gp, gplant = read_log(good)
    bp, bplant = read_log(bad)
    sel = lambda rows: [r for r in rows if 34 <= r[0] <= 54]
    fig, ax = plt.subplots(figsize=(9, 3.4))
    ax.plot(*zip(*[(p[0], p[1]) for p in sel(bplant)]), color=RED, lw=2.5,
            label="unchecked: true temperature")
    ax.plot(*zip(*[(r[0], r[1]) for r in sel(bp)]), color=RED, lw=1, ls=":",
            label="unchecked: measured (0xFFFF = −0.06 °C)")
    ax.plot(*zip(*[(p[0], p[1]) for p in sel(gplant)]), color=CYAN, lw=2.5,
            label="checked: true temperature (safe state)")
    ax.axhline(40, color=GRAY, lw=0.8, ls="--")
    shade(ax, labels=True, faults=((SENSOR_FAULT, "sensor fault"),))
    ax.set_xlim(34, 54)
    ax.set_ylabel("°C")
    ax.set_xlabel("simulated time [s]")
    ax.legend(loc="lower left", frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(out)


def load_vcd(path):
    t, ch, ids = 0, {"_seq": {}}, {}
    for n, line in enumerate(open(path)):
        line = line.strip()
        if line.startswith("$var"):
            p = line.split()
            ids[p[3]] = p[4]
        elif line.startswith("#"):
            t = int(line[1:])
        elif line[:1] in "01" and line[1:] in ids:
            ch.setdefault(ids[line[1:]], []).append((t, int(line[0])))
            ch["_seq"].setdefault(ids[line[1:]], []).append(n)
    return ch


def wave(edges, t0, t1):
    """Step curve of one channel between t0 and t1 (ns)."""
    level = 0
    xs, ys = [], []
    for t, v in edges:
        if t < t0:
            level = v
            continue
        if t > t1:
            break
        xs += [t, t]
        ys += [level, v]
        level = v
    return [t0] + xs + [t1], [ys[0] if ys else level] + ys + [level]


def decode_i2c(scl, sda, t0, t1):
    """Minimal I2C decoder: returns [(t_start, t_end, text)] for each byte."""
    # sort by time only: changes with the same time stamp keep their order in the file
    events = sorted([(t, i, "C", v) for i, (t, v) in scl] + [(t, i, "D", v) for i, (t, v) in sda])
    c = d = 1
    out, bits, start = [], [], None
    for t, _, kind, v in events:
        if kind == "D":
            if c and t0 <= t <= t1:
                if d == 1 and v == 0:
                    out.append((t, t, "S"))
                    bits, start = [], None
                elif d == 0 and v == 1:
                    out.append((t, t, "P"))
            d = v
        else:
            if v == 1 and c == 0 and t0 <= t <= t1:      # rising SCL: sample SDA
                if not bits:
                    start = t
                bits.append(d)
                if len(bits) == 9:
                    value = int("".join(map(str, bits[:8])), 2)
                    out.append((start, t, f"{value:02X}" + (" A" if bits[8] == 0 else " N")))
                    bits = []
            c = v
    return out


def traces(ax, ch, rows, t0, t1, scale, unit, label_dx):
    for i, (d, name) in enumerate(rows):
        xs, ys = wave(ch[d], t0, t1)
        ax.plot([(x - t0) / scale for x in xs], [y * 0.7 - i for y in ys], color=VIOLET, lw=0.8)
        ax.text(-label_dx, -i + 0.35, name, ha="right", va="center", fontsize=10)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlim(0, (t1 - t0) / scale)
    ax.set_xlabel(unit, fontsize=10)


def fig_logic(vcd, out):
    ch = load_vcd(vcd)
    fig, (a1, a2, a3) = plt.subplots(3, 1, figsize=(10, 5.6),
                                     gridspec_kw={"height_ratios": [1.1, 0.8, 1.1]})
    # 1: bus activity and tachometer over 700 ms (steady state)
    t0 = 19.70e9
    traces(a1, ch, [("D0", "SCL"), ("D1", "SDA"), ("D4", "TACH")], t0, t0 + 0.7e9, 1e6,
           f"ms after t = {t0 / 1e9:.1f} s:  temperature read every 100 ms, LCD update "
           "every 500 ms (95 ms bus time), tachometer 40 Hz = 1200 rpm", 8)
    # 2: the two PWM signals over 4 ms
    p0 = 19.90e9
    traces(a2, ch, [("D2", "HEAT"), ("D3", "FAN")], p0, p0 + 4e6, 1e3,
           "µs:  heater PWM 53 %, fan PWM 40 %, 1 kHz", 45)
    # 3: one TMP102 read, decoded
    z0 = [t for t, v in ch["D0"] if t > 20.0e9][0] - 20000
    z1 = z0 + 520000
    traces(a3, ch, [("D0", "SCL"), ("D1", "SDA")], z0, z1, 1e3,
           "µs:  S 90 (0x48 write) 00 (pointer = temperature) S 91 (0x48 read) MSB LSB P", 6)
    seq = {d: list(zip(ch["_seq"][d], ch[d])) for d in ("D0", "D1")}
    for s, e, text in decode_i2c(seq["D0"], seq["D1"], z0, z1):
        if text in ("S", "P"):
            a3.text((s - z0) / 1e3, -1.6, text, ha="center", fontsize=10, color=RED)
        else:
            a3.add_patch(plt.Rectangle(((s - z0) / 1e3 - 4, -2.0), (e - s) / 1e3 + 8, 0.45,
                                       color=CYAN, alpha=0.25, lw=0))
            a3.text((s + e) / 2e3 - z0 / 1e3, -1.77, text, ha="center", va="center", fontsize=10)
    a3.set_ylim(-2.1, 0.9)
    fig.tight_layout()
    fig.savefig(out)


if __name__ == "__main__":
    data, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    fig_faults(data / "good", outdir / "chamber_faults.pdf")
    fig_nocheck(data / "good", data / "bad", outdir / "chamber_nocheck.pdf")
    fig_logic(data / "la.vcd", outdir / "chamber_logic.pdf")
