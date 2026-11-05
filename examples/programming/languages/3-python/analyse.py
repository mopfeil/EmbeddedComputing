"""What Python makes easy: find the cause of a vibration in 10 lines.

Read a sensor log, compute the frequency spectrum (FFT), print the three
strongest frequencies and plot signal and spectrum. In C on a PC this needs
a CSV parser, an FFT library and a plotting library - hundreds of lines.

    python make_data.py      # creates vibration.csv (simulated motor)
    python analyse.py        # analysis, writes vibration.png
"""
import matplotlib.pyplot as plt
import numpy as np

t_ms, raw = np.loadtxt("vibration.csv", delimiter=",", skiprows=1, unpack=True)
fs = 1000 / np.mean(np.diff(t_ms))             # sample rate from the time stamps
a = raw / 16384                                # raw -> g (+-2 g range)

spectrum = np.abs(np.fft.rfft(a - a.mean())) * 2 / len(a)   # amplitude in g
freq = np.fft.rfftfreq(len(a), 1 / fs)

for i in np.argsort(spectrum)[-3:][::-1]:       # the three highest peaks
    print(f"{freq[i]:6.1f} Hz   {spectrum[i]:.3f} g")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 5), layout="constrained")
ax1.plot(t_ms[:300], a[:300]); ax1.set(xlabel="time [ms]", ylabel="acceleration [g]")
ax2.plot(freq, spectrum); ax2.set(xlabel="frequency [Hz]", ylabel="amplitude [g]")
fig.savefig("vibration.png", dpi=150)
plt.show()
