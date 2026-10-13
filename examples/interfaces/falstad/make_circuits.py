"""Generate the Falstad CircuitJS circuits of the worksheet "GPIO output stages".

    pip install lzstring
    python3 make_circuits.py

writes the circuit files (*.txt, CircuitJS XML format) into this folder and
figures/falstad/links.tex (links that open each circuit on falstad.com) for
Worksheet_IO_Ports.tex. check_circuits.py runs them in a headless browser.
"""
import os, sys
from xml.sax.saxutils import quoteattr
class Circ:
    def __init__(s, ts, mts=None, ic=10.2, f=1, vr=5, cb=50):
        s.head = dict(f=f, ts=ts, ic=ic, cb=cb, pb=50, vr=vr)
        if mts: s.head['mts'] = mts
        s.models, s.elms, s.adjs, s.scopes, s.names = [], [], [], [], {}
    def model(s, tag, **a): s.models.append((tag, a))
    def add(s, tag, x1, y1, x2, y2, name=None, f=0, **a):
        s.elms.append((tag, dict(x=f"{x1} {y1} {x2} {y2}", f=f, **a)))
        if name: s.names[name] = len(s.elms) - 1
        return len(s.elms) - 1
    def w(s, *pts):                    # polyline of wires
        for (a, b), (c, d) in zip(pts, pts[1:]): s.add('w', a, b, c, d)
    def adj(s, elm, en, text, mn, mx, log=False, share=None):
        d = dict(e=s.names[elm], ei=0, en=en, mn=mn, mx=mx, st=text)
        if log: d['log'] = 1
        if share is not None: d['ss'] = share
        s.adjs.append(d); return len(s.adjs) - 1
    def scope(s, plots, sp=64, f=0, p=None, **a):
        """plots: list of (elmname, value, scale); value 0=V, 3=I, 7=P"""
        s.scopes.append((dict(en=s.names[plots[0][0]], sp=sp, f=f, p=len(s.scopes) if p is None else p, **a), plots))
    def xml(s):
        at = lambda d: " ".join(f"{k}={quoteattr(str(v))}" for k, v in d.items())
        out = [f"<cir {at(s.head)}>"]
        out += [f"  <{t} {at(a)}/>" for t, a in s.models]
        out += [f"  <{t} {at(a)}/>" for t, a in s.elms]
        out += [f"  <adj {at(a)}/>" for a in s.adjs]
        for a, plots in s.scopes:
            out.append(f"  <o {at(a)}>")
            for n, v, sc in plots:
                d = {} if s.names[n] == a['en'] else dict(e=s.names[n])
                d.update(v=v, sc=sc); out.append(f"    <p {at(d)}/>")
            out.append("  </o>")
        return "\n".join(out + ["</cir>"]) + "\n"

# GPIO output transistors: R_on ~ 1/(beta (VDD-Vt)) with VDD = 3.3 V
def gpio_models(c):
    c.model('mm', nm="gpio-nmos", f=0, vt=0.6, be=0.012, sb=0, dsy=0, bd=1, bt=0, sbd=0)
    c.model('mm', nm="gpio-pmos", f=0, vt=0.6, be=0.008, sb=0, dsy=0, bd=1, bt=0, sbd=0)
def label(c, x1, y1, x2, y2, text):
    c.add('ln', x1, y1, x2, y2, name=text, f=4, te=text)

def title(c, t, *lines):
    c.add('x', 48, 32, 0, 0, si=20, te=t)
    for i, l in enumerate(lines): c.add('x', 48, 64 + 24*i, 0, 0, si=14, te=l)

def pushpull(c, x, y, inp=None, name="", vdd=True, fast=False):
    """Push-pull stage: gates at (x,y), output node (x+64,y), PMOS source at (x+64,y-64)."""
    c.add('f', x, y-48, x+64, y-48, name=name+"P", f=1, mo="gpio-pmos-fast" if fast else "gpio-pmos")
    c.add('f', x, y+48, x+64, y+48, name=name+"N", f=0, mo="gpio-nmos-fast" if fast else "gpio-nmos")
    c.w((x, y-48), (x, y), (x, y+48))
    c.w((x+64, y-32), (x+64, y), (x+64, y+32))
    c.add('g', x+64, y+64, x+64, y+96)
    if vdd: c.add('R', x+64, y-64, x+64, y-96, wf=0, maxv=3.3)
    if inp: c.w(inp, (x, y))

def A():
    c = Circ(ts=2e-7, mts=1e-7); gpio_models(c)
    title(c, "A: Push-pull GPIO output characteristic (curve tracer)",
          "Logic input = output register bit. The sweep source forces V(PIN) from -0.5 V to 3.8 V.",
          "Left scope: X = V(PIN), Y = pin current (> 0: out of the pin). Right scope: power in PMOS and NMOS.")
    c.add('L', 128, 256, 80, 256, name="in", p=1, hi=3.3, lo=0)
    c.add('I', 128, 256, 176, 256, sl=0.5, hi=3.3)
    pushpull(c, 240, 256, (176, 256))
    c.w((304, 256), (368, 256))
    label(c, 368, 256, 368, 224, "PIN")
    c.add('Ammeter', 368, 256, 464, 256, name="amm", f=3, me=0, sc=0)
    c.add('v', 464, 384, 464, 256, name="sw", wf=3, fr=250, maxv=2.15, bias=1.65)
    c.add('g', 464, 384, 464, 416)
    c.scope([("sw", 0, 4), ("amm", 3, 0.05)], f=2|64|128, sp=1)
    c.scope([("P", 7, 0.1), ("N", 7, 0.1)], f=2, sp=8)
    return c

def B():
    c = Circ(ts=1e-10, mts=5e-11); gpio_models(c)
    title(c, "B: Push-pull output switching a capacitive load",
          "The square wave is the program toggling the pin; the predriver slew rate sets how fast the gates switch.",
          "Left scope: gate G and PIN. Right scope: supply current and its average. Sliders on the right.")
    c.add('R', 96, 320, 48, 320, name="clk", wf=2, fr=1e6, maxv=1.65, bias=1.65)
    c.w((96, 320), (128, 320))
    c.add('I', 128, 320, 176, 320, name="drv", sl=2, hi=3.3)
    c.w((176, 320), (208, 320))
    label(c, 208, 320, 208, 288, "G")
    pushpull(c, 240, 320, (208, 320), vdd=False)
    c.add('R', 304, 176, 304, 144, wf=0, maxv=3.3)
    c.add('Ammeter', 304, 176, 304, 256, name="isup", f=3, me=0, sc=0)
    c.w((304, 320), (368, 320), (432, 320))
    label(c, 368, 320, 368, 288, "PIN")
    c.add('c', 432, 320, 432, 400, name="cl", c=1e-10)
    c.add('g', 432, 400, 432, 432)
    c.adj("cl", "Capacitance (F)", "Load capacitance C_L", 1e-12, 1e-9, log=True)
    c.adj("clk", "Frequency (Hz)", "Toggle frequency", 1e5, 5e7, log=True)
    c.adj("drv", "Slew Rate (V/ns)", "Predriver slew rate (V/ns)", 0.01, 5, log=True)
    c.scope([("G", 0, 4), ("PIN", 0, 4)], f=2, sp=32)
    c.scope([("isup", 3, 0.05)], f=1 | (1 << 17), sp=32)
    return c

def C():
    c = Circ(ts=1e-9, mts=1e-9); gpio_models(c)
    title(c, "C: Two push-pull outputs on one line (bus contention)",
          "Both pins are wired together, e.g. two devices on a shared line or a pin shorted to a neighbour.",
          "Set A = H and B = L (or vice versa). Scope: line current, power in the PMOS of A and the NMOS of B.")
    c.add('L', 128, 256, 80, 256, name="inA", p=1, hi=3.3, lo=0)
    c.add('I', 128, 256, 176, 256, sl=0.5, hi=3.3)
    pushpull(c, 240, 256, (176, 256), name="A")
    c.add('L', 528, 256, 480, 256, name="inB", p=0, hi=3.3, lo=0)
    c.add('I', 528, 256, 576, 256, sl=0.5, hi=3.3)
    pushpull(c, 640, 256, (576, 256), name="B")
    c.w((304, 256), (336, 256))
    label(c, 336, 256, 336, 224, "PIN_A")
    c.w((336, 256), (336, 416))
    c.add('Ammeter', 336, 416, 528, 416, name="amm", f=3, me=0, sc=0)
    c.w((528, 416), (736, 416), (736, 256), (704, 256))
    label(c, 736, 256, 736, 224, "PIN_B")
    c.scope([("amm", 3, 0.05)], f=1, sp=16)
    c.scope([("AP", 7, 0.1), ("BN", 7, 0.1)], f=2, sp=16)
    return c

def D():
    c = Circ(ts=2e-9, mts=1e-9); gpio_models(c)
    title(c, "D: Open-drain bus (I2C-like) versus push-pull",
          "Device 1 sends a clock, device 2 can hold the bus low (wired AND). Pull-up R_P and bus capacitance C_bus are sliders.",
          "The push-pull stage below drives the same capacitance for comparison. Scope 1: BUS and PP. Scope 2: current in R_P.")
    c.add('R', 96, 288, 48, 288, name="clk", wf=2, fr=1e5, maxv=1.65, bias=1.65)
    c.w((96, 288), (128, 288))
    c.add('I', 128, 288, 176, 288, sl=0.5, hi=3.3)
    c.w((176, 288), (240, 288))
    c.add('f', 240, 288, 304, 288, name="N1", f=0, mo="gpio-nmos")
    c.add('g', 304, 304, 304, 336)
    c.add('x', 224, 368, 0, 0, si=14, te="device 1")
    c.add('L', 400, 288, 352, 288, name="in2", p=1, hi=3.3, lo=0)
    c.add('I', 400, 288, 448, 288, sl=0.5, hi=3.3)
    c.add('f', 448, 288, 512, 288, name="N2", f=0, mo="gpio-nmos")
    c.add('g', 512, 304, 512, 336)
    c.add('x', 432, 368, 0, 0, si=14, te="device 2")
    c.add('R', 400, 144, 400, 112, wf=0, maxv=3.3)
    c.add('r', 400, 144, 400, 256, name="rp", r=4700)
    c.w((304, 272), (304, 256), (400, 256), (512, 256), (576, 256), (640, 256))
    c.w((512, 272), (512, 256))
    label(c, 576, 256, 576, 224, "BUS")
    c.add('c', 640, 256, 640, 336, name="cb", c=2e-10)
    c.add('g', 640, 336, 640, 368)
    # push-pull reference, same clock
    c.w((96, 288), (96, 512), (128, 512))
    c.add('I', 128, 512, 176, 512, sl=0.5, hi=3.3)
    pushpull(c, 240, 512, (176, 512))
    c.w((304, 512), (576, 512), (640, 512))
    label(c, 576, 512, 576, 480, "PP")
    c.add('c', 640, 512, 640, 592, name="cpp", c=2e-10)
    c.add('g', 640, 592, 640, 624)
    c.add('x', 224, 640, 0, 0, si=14, te="push-pull reference")
    k = c.adj("cb", "Capacitance (F)", "Bus capacitance C_bus", 1e-11, 1e-9, log=True)
    c.adj("cpp", "Capacitance (F)", "", 1e-11, 1e-9, log=True, share=k)
    c.adj("rp", "Resistance (ohms)", "Pull-up R_P", 220, 47000, log=True)
    c.adj("clk", "Frequency (Hz)", "Clock frequency", 1e4, 2e6, log=True)
    c.scope([("BUS", 0, 4), ("PP", 0, 4)], f=2, sp=16)
    c.scope([("rp", 3, 0.01)], f=1, sp=16)
    return c

def E():
    c = Circ(ts=1e-7, mts=1e-7); gpio_models(c)
    c.model('dm', nm="ideal-reg", f=0, **{"is": 1e-14}, rs=0, n=0.05, bv=0)
    title(c, "E: Open drain with a 5 V pull-up: maximum pin voltage",
          "Both NMOS are switched by the same signal. PIN1 is a normal 3.3 V GPIO in open-drain mode,",
          "PIN2 a 5 V-tolerant open-drain pin. The regulator can only source current (diode).")
    c.add('v', 96, 352, 96, 192, name="reg", wf=0, maxv=3.3)
    c.add('g', 96, 352, 96, 384)
    c.add('d', 96, 192, 176, 192, mo="ideal-reg")
    c.add('x', 48, 416, 0, 0, si=14, te="3.3 V regulator")
    c.w((176, 192), (208, 192), (272, 192), (336, 192), (400, 192))
    label(c, 176, 192, 176, 160, "VDD")
    c.add('c', 208, 192, 208, 272, name="cdd", c=1e-6)
    c.add('g', 208, 272, 208, 304)
    c.add('r', 272, 192, 272, 272, name="rmcu", r=33000)
    c.add('g', 272, 272, 272, 304)
    c.add('x', 224, 336, 0, 0, si=14, te="MCU load")
    c.add('Ammeter', 400, 256, 400, 192, name="inj", f=3, me=0, sc=0)
    c.add('f', 336, 272, 400, 272, name="P1", f=1, mo="gpio-pmos")
    c.w((336, 272), (336, 192))
    c.add('f', 336, 368, 400, 368, name="N1", f=0, mo="gpio-nmos")
    c.add('g', 400, 384, 400, 416)
    c.w((400, 288), (400, 320), (400, 352))
    c.w((400, 320), (464, 320))
    label(c, 464, 320, 464, 352, "PIN1")
    c.add('R', 464, 240, 464, 208, wf=0, maxv=5)
    c.add('r', 464, 240, 464, 320, name="rpu1", r=4700)
    c.add('R', 240, 480, 192, 480, name="clk", wf=2, fr=1e4, maxv=1.65, bias=1.65)
    c.add('I', 240, 480, 288, 480, sl=0.5, hi=3.3)
    c.w((288, 480), (336, 480), (336, 368))
    c.w((336, 480), (592, 480), (592, 368))
    c.add('f', 592, 368, 656, 368, name="N2", f=0, mo="gpio-nmos")
    c.add('g', 656, 384, 656, 416)
    c.w((656, 352), (656, 320), (720, 320))
    label(c, 720, 320, 720, 352, "PIN2")
    c.add('R', 656, 240, 656, 208, wf=0, maxv=5)
    c.add('r', 656, 240, 656, 320, name="rpu2", r=4700)
    c.add('x', 304, 544, 0, 0, si=14, te="normal GPIO, open-drain mode")
    c.add('x', 576, 544, 0, 0, si=14, te="5 V-tolerant open-drain pin")
    k = c.adj("rpu1", "Resistance (ohms)", "Pull-ups to 5 V", 470, 47000, log=True)
    c.adj("rpu2", "Resistance (ohms)", "", 470, 47000, log=True, share=k)
    c.adj("rmcu", "Resistance (ohms)", "MCU load (3.3 V / I_DD)", 1000, 1e6, log=True)
    c.scope([("PIN1", 0, 5), ("PIN2", 0, 5)], f=2, sp=64)
    c.scope([("VDD", 0, 5)], f=2, sp=64)
    c.scope([("inj", 3, 0.001)], f=1, sp=64)
    return c

def F():
    c = Circ(ts=2e-7, mts=1e-7)
    c.model('dm', nm="zener-24V", f=0, **{"is": 1.7143528192808883e-7}, rs=0, n=2, bv=24)
    title(c, "F: Open-collector driver for a 12 V relay coil or lamp",
          "The 3.3 V GPIO switches an NPN transistor (beta = 100) through R_B. The load selector chooses relay coil or lamp.",
          "Close 'flyback' to add the free-wheeling diode; open 'bypass' to put a 24 V zener in series with it.")
    c.add('R', 400, 128, 400, 96, wf=0, maxv=12)
    c.w((400, 128), (464, 128), (624, 128))
    c.add('Ammeter', 400, 128, 400, 176, name="icoil", f=3, me=0, sc=0)
    c.add('l', 400, 176, 400, 240, name="coil", f=2, l=0.1)       # f=2: backward Euler, avoids
    # numerical ringing when the transistor charges the winding capacitance within one time step
    c.add('r', 400, 240, 400, 304, name="rcoil", r=400)
    c.w((400, 176), (336, 176)); c.w((336, 304), (400, 304))
    c.add('c', 336, 176, 336, 304, name="cpar", f=2, c=1e-9)
    c.add('x', 208, 240, 0, 0, si=14, te="relay coil")
    c.add('x', 208, 264, 0, 0, si=14, te="0.1 H, 400 Ohm")
    c.w((400, 304), (464, 304))
    c.add('d', 464, 304, 464, 240, mo="1N4148")
    c.add('z', 464, 176, 464, 240, name="zd", mo="zener-24V")
    c.w((464, 240), (528, 240)); c.w((528, 176), (464, 176))
    c.add('s', 528, 240, 528, 176, name="bypass", p=0, mo=0)
    c.add('x', 544, 216, 0, 0, si=14, te="bypass")
    c.add('s', 464, 176, 464, 128, name="flyback", p=1, mo=0)
    c.add('x', 480, 168, 0, 0, si=14, te="flyback")
    c.add('r', 624, 128, 624, 304, name="lamp", r=29)
    c.add('x', 640, 216, 0, 0, si=14, te="lamp 12 V / 5 W")
    c.add('S', 512, 400, 512, 336, name="sel", p=0, mo=0, li=0, th=2)
    c.w((496, 336), (496, 320), (400, 320), (400, 304))
    c.w((528, 336), (528, 320), (624, 320), (624, 304))
    c.add('t', 448, 448, 512, 448, name="q", pn=1, be=100, mo="default")
    c.w((512, 432), (512, 416), (512, 400))
    label(c, 512, 416, 576, 416, "C")
    c.add('g', 512, 464, 512, 496)
    c.add('R', 256, 448, 208, 448, name="gpio", wf=2, fr=200, maxv=1.65, bias=1.65)
    c.add('r', 256, 448, 448, 448, name="rb", r=1000)
    c.adj("rb", "Resistance (ohms)", "Base resistor R_B", 100, 1e5, log=True)
    c.adj("gpio", "Frequency (Hz)", "Switching frequency", 10, 1000, log=True)
    c.scope([("C", 0, 50)], f=2, sp=64, p=0)
    c.scope([("icoil", 3, 0.05)], f=1, sp=64)
    c.scope([("q", 7, 1)], f=0, sp=64)
    return c

def G():
    c = Circ(ts=1e-11, mts=1e-11)
    # highest drive strength / fast slew setting: R_on about 12 and 15 Ohm
    c.model('mm', nm="gpio-nmos-fast", f=0, vt=0.6, be=0.03, sb=0, dsy=0, bd=1, bt=0, sbd=0)
    c.model('mm', nm="gpio-pmos-fast", f=0, vt=0.6, be=0.025, sb=0, dsy=0, bd=1, bt=0, sbd=0)
    title(c, "G: Fast push-pull edges on a 50 Ohm PCB trace",
          "The trace (1 ns delay, about 15 cm on FR4) ends at the input of another chip: 5 pF plus ESD diodes.",
          "Output in its fastest setting (R_on about 12-15 Ohm). Sliders: series resistor R_S, slew rate. Scope: PIN and RX.")
    c.add('R', 96, 256, 48, 256, name="clk", wf=2, fr=1e7, maxv=1.65, bias=1.65)
    c.w((96, 256), (128, 256))
    c.add('I', 128, 256, 176, 256, name="drv", sl=5, hi=3.3)
    pushpull(c, 240, 256, (176, 256), fast=True)
    c.w((304, 256), (336, 256))
    label(c, 336, 256, 336, 224, "PIN")
    c.add('r', 336, 256, 432, 256, name="rs", r=0.1)
    c.add('tl', 432, 256, 688, 256, name="tl", de=1e-9, im=50, wi=32)
    c.add('g', 432, 288, 432, 320); c.add('g', 688, 288, 688, 320)
    c.w((688, 256), (752, 256), (816, 256), (880, 256))
    label(c, 752, 256, 752, 224, "RX")
    c.add('c', 880, 256, 880, 336, name="cin", c=5e-12)
    c.add('g', 880, 336, 880, 368)
    c.add('d', 816, 256, 816, 192, name="desd", mo="default")
    c.add('R', 816, 192, 816, 160, wf=0, maxv=3.3)
    c.add('d', 816, 320, 816, 256, name="desd2", mo="default")
    c.add('g', 816, 320, 816, 352)
    c.add('x', 736, 400, 0, 0, si=14, te="receiver input")
    c.adj("rs", "Resistance (ohms)", "Series resistor R_S", 0.1, 100)
    c.adj("drv", "Slew Rate (V/ns)", "Output slew rate (V/ns)", 0.1, 5, log=True)
    c.scope([("PIN", 0, 5), ("RX", 0, 5)], f=2, sp=6)
    c.scope([("desd", 3, 0.05), ("desd2", 3, 0.05)], f=1, sp=6)
    return c

CIRCUITS = {
    "A": "A_pushpull_characteristic", "B": "B_pushpull_capacitive_load",
    "C": "C_bus_contention", "D": "D_open_drain_bus", "E": "E_open_drain_overvoltage",
    "F": "F_open_collector_inductive", "G": "G_transmission_line",
}
HERE = os.path.dirname(os.path.abspath(__file__))
LECTURE = os.path.normpath(os.path.join(HERE, "..", "..", ".."))

def url(xml):
    import lzstring
    return ("https://www.falstad.com/circuit/circuitjs.html?ctz="
            + lzstring.LZString().compressToEncodedURIComponent(xml))

if __name__ == "__main__":
    links = ["% generated by examples/interfaces/falstad/make_circuits.py"]
    for key, name in CIRCUITS.items():
        xml = globals()[key]().xml()
        open(os.path.join(HERE, name + ".txt"), "w").write(xml)
        links.append(r"\def\link%s{%s}" % (key, url(xml)))
        print(name + ".txt")
    open(os.path.join(LECTURE, "figures", "falstad", "links.tex"), "w").write("\n".join(links) + "\n")
