"""Create vibration.csv: a simulated acceleration log of an electric motor.

The data looks like the output of a data logger with an MPU-6050 sensor
(see chapter Interfaces): 2 s at 1 kHz sample rate, raw 16 bit values,
+-2 g range = 16384 LSB/g. Hidden in the noise:
  - 24.5 Hz  rotation of the motor (1470 rpm), imbalance
  - 50 Hz    mains hum picked up by the cable
  - 137 Hz   a damaged ball bearing (small amplitude)
"""
import csv
import math
import random

FS = 1000                     # sample rate in Hz
random.seed(1)

with open("vibration.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["time_ms", "accel_z_raw"])
    for n in range(2 * FS):
        t = n / FS
        g = (1.0                                        # gravity
             + 0.30 * math.sin(2 * math.pi * 24.5 * t)  # imbalance
             + 0.10 * math.sin(2 * math.pi * 50.0 * t)  # mains hum
             + 0.06 * math.sin(2 * math.pi * 137.0 * t) # bearing damage
             + random.gauss(0, 0.25))                   # noise
        w.writerow([n, round(g * 16384)])

print("vibration.csv written: 2000 samples")
