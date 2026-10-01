# Examples for chapter "Cyber-Physical Systems"

* `HDE.mo`, `Pendulum.mo`, `RLC1.mo`, `classes.mo`: the Modelica models of the
  chapter (open them in OpenModelica / OMEdit).
* `simulate.py`: the same models simulated with Python (numpy, scipy,
  matplotlib); creates `cps_hde.pdf`, `cps_pendulum.pdf`, `cps_rlc.pdf`, the
  plots in the lecture. Runs on a PC or on Replit: `python3 simulate.py`.

Tested: `simulate.py` runs with Python 3.12 / scipy 1.11 (RLC end value
i_L = 0.240 A = Vb/R as expected). The Modelica files were corrected by hand
(pendulum: `der(x) = vx`, `g = 9.81`; classes: three distinct points) but not
run in OpenModelica here.
