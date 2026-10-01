"""The models of the chapter Cyber-Physical Systems, simulated with Python
(numpy/scipy) - the same equations as in the Modelica files.
Creates the plots used in the lecture (PDF). Runs on a PC or on Replit."""
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.integrate import solve_ivp

def save(fig, name):
    fig.tight_layout()
    fig.savefig(name)
    print("written", name)

# 1. der(x) = -a*x, x(0) = 1
a = 1.0
sol = solve_ivp(lambda t, x: -a * x, (0, 5), [1.0], dense_output=True, rtol=1e-8)
t = np.linspace(0, 5, 300)
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(t, sol.sol(t)[0], label="x (simulated)")
ax.plot(t, np.exp(-a * t), "--", label="exp(-a t) (exact)")
ax.set_xlabel("time [s]"); ax.set_ylabel("x"); ax.grid(True); ax.legend()
save(fig, "cps_hde.pdf")

# 2. Pendulum. The DAE of the Modelica model is index 3; for the Python
# simulation we use the equivalent ODE in the angle phi:
#    x = L sin(phi), y = -L cos(phi), phi'' = -(g/L) sin(phi)
m, g, L = 1.0, 9.81, 0.5
phi0 = np.pi / 2                       # x(0) = 0.5 = L, y(0) = 0: rod horizontal
sol = solve_ivp(lambda t, s: [s[1], -(g / L) * np.sin(s[0])], (0, 5), [phi0, 0.0],
                dense_output=True, rtol=1e-9, atol=1e-9)
t = np.linspace(0, 5, 1000)
phi = sol.sol(t)[0]
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(t, L * np.sin(phi), label="x")
ax.plot(t, -L * np.cos(phi), label="y")
ax.set_xlabel("time [s]"); ax.set_ylabel("position [m]"); ax.grid(True); ax.legend(loc="lower right")
save(fig, "cps_pendulum.pdf")

# 3. RLC circuit: C dV/dt = i_L - V/R, L di_L/dt = Vb - V
Vb, Lh, R, C = 24.0, 1.0, 100.0, 1e-3
def rlc(t, s):
    V, iL = s
    return [(iL - V / R) / C, (Vb - V) / Lh]
sol = solve_ivp(rlc, (0, 1.5), [0.0, 0.0], dense_output=True, rtol=1e-8, max_step=1e-3)
t = np.linspace(0, 1.5, 1500)
V, iL = sol.sol(t)
iR = V / R
iC = iL - iR
fig, ax = plt.subplots(figsize=(6, 3))
ax.plot(t, iL, label="i_L"); ax.plot(t, iR, label="i_R"); ax.plot(t, iC, label="i_C")
ax.set_xlabel("time [s]"); ax.set_ylabel("current [A]"); ax.grid(True); ax.legend()
save(fig, "cps_rlc.pdf")
print(f"RLC: final i_L = {iL[-1]:.3f} A (expected Vb/R = {Vb / R:.3f} A)")
