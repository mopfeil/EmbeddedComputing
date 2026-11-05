"""The price of the simplicity: Python loops are slow, NumPy is fast.

The same task, the mean of one million sensor values, three times:
a Python loop, the built-in sum(), and NumPy (whose inner loop is C).
"""
import time

import numpy as np

values = list(range(1_000_000))
array = np.array(values, dtype=np.int32)


def loop_mean(v):
    s = 0
    for x in v:
        s += x
    return s / len(v)


for name, f, data in [("Python loop", loop_mean, values),
                      ("sum()", lambda v: sum(v) / len(v), values),
                      ("NumPy", np.mean, array)]:
    t0 = time.perf_counter()
    result = f(data)
    dt = time.perf_counter() - t0
    print(f"{name:12s} {dt * 1e3:8.2f} ms   ({dt * 1e9 / len(values):5.1f} ns per value)")
