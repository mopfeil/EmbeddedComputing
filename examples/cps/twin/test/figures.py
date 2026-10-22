#!/usr/bin/env python3
"""Figure for the lecture from an end-to-end run (test/leak.yaml).

Expects in <datadir>:
  device.log   wokwi-cli --scenario test/leak.yaml --timeout 150000 --serial-log-file device.csv . > device.log
               (the tank chip prints the true leak flow there)
  tank1.csv    the twin server's log of the same run (<server dir>/log/tank1.csv)

usage: figures.py <datadir> <outdir>
"""
import csv
import re
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from pathlib import Path

VIOLET, CYAN, RED, GRAY, ORANGE = "#6638b6", "#00a9ce", "#c0392b", "#888888", "#e69500"
FONTS = Path(__file__).resolve().parents[4] / "fonts"
for f in FONTS.glob("BarlowSemiCondensed-*.otf"):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({"font.family": "Barlow Semi Condensed", "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False})


def main(data, out):
    truth = []                                   # (t, true leak L/s) from the tank chip
    for line in open(data / "device.log", errors="replace"):
        m = re.match(r"\[chip-tank\] tank (\d+) ms: .* leak=([\d.]+) L/s", line)
        if m:
            truth.append((int(m[1]) / 1000, float(m[2])))
    rows = list(csv.DictReader(open(data / "tank1.csv")))
    col = lambda k: [float(r[k]) for r in rows]
    t = col("t")
    leak_on = next(tt for tt, q in truth if q > 0)
    alarm_on = next(float(r["t"]) for r in rows if r["alarm"] == "1")
    valve = alarm_on + 20                        # the scenario opens the valve 20 s after the alarm

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 4.6), sharex=True, height_ratios=[3, 2])
    ax1.plot(t, col("h"), color=CYAN, lw=2, label="measured level")
    ax1.plot(t, col("h_model"), color=ORANGE, lw=1.5, ls="--", label="model without measurements")
    ax1.plot(t, col("sp"), color=GRAY, lw=1, label="setpoint on the device")
    ax1.set_ylabel("level in m")
    ax1.set_ylim(0, 1)
    ax1.legend(loc="upper left", frameon=False, fontsize=9)
    ax2.plot([a for a, _ in truth], [b for _, b in truth], color=GRAY, lw=1.5, label="true leak (tank chip)")
    ax2.plot(t, col("leak"), color=RED, lw=2, label="leak estimated by the twin")
    ax2.plot(t, col("q"), color=CYAN, lw=1, label="measured outlet flow")
    ax2.axhline(0.15, color=RED, lw=0.8, ls=":")
    ax2.set_ylabel("flow in L/s")
    ax2.set_xlabel("device time in s")
    ax2.legend(loc="upper left", frameon=False, fontsize=9)
    for ax in (ax1, ax2):
        ax.axvline(leak_on, color=RED, lw=0.8)
        ax.axvline(alarm_on, color=VIOLET, lw=0.8)
        ax.axvline(valve, color=CYAN, lw=0.8)
    ax1.text(leak_on, 0.95, " leak opens", color=RED, fontsize=9, va="top", ha="right")
    ax1.text(alarm_on, 0.95, f" alarm (+{alarm_on - leak_on:.1f} s)", color=VIOLET, fontsize=9, va="top")
    ax1.text(valve, 0.8, " consumer valve 0.5 to 0.9", color=CYAN, fontsize=9, va="top")
    fig.tight_layout()
    fig.savefig(out / "cps_twin_leak.pdf")
    print(f"leak at {leak_on:.1f} s, alarm at {alarm_on:.1f} s")


main(Path(sys.argv[1]), Path(sys.argv[2]))
