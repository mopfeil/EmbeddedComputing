"""Run the worksheet circuits headless on falstad.com and print the values used
in the solutions; 'figures' exports the schematics as PDF.

    python3 check_circuits.py [A ... J] [figures [A ... J]]
"""
import os, re, sys, time
import numpy as np
from playwright.sync_api import sync_playwright
import make_circuits as gen
from make_circuits import url, LECTURE

_b = None
def browser():
    global _b
    if _b is None:
        _b = sync_playwright().start().chromium.launch()
    return _b

def run(xml, tend, nodes=(), currents=(), every=1):
    """Simulate until tend; returns rows [t, V(labelled nodes)..., I(elements)...] for every time step."""
    pg = browser().new_page()
    pg.goto(url(xml)); pg.wait_for_function("window.CircuitJS1 !== undefined", timeout=60000)
    pg.evaluate("""([nodes, cur, every]) => { window.rec=[]; let k=0; const E=CircuitJS1.getElements();
      CircuitJS1.ontimestep = function(s){ if (k++ % every) return; var r=[s.getTime()];
        for (const n of nodes) r.push(s.getNodeVoltage(n));
        for (const i of cur) r.push(E[i].getCurrent()); rec.push(r); }; }""", [list(nodes), list(currents), every])
    t0 = time.time()
    while pg.evaluate("CircuitJS1.getTime()") < tend and time.time() - t0 < 900:
        time.sleep(0.3)
    pg.evaluate("CircuitJS1.setSimRunning(false)")
    rec = np.array(pg.evaluate("rec")); pg.close()
    return rec

def figures(keys):
    """Schematic without texts, scopes and sliders, white background, as PDF."""
    for k in keys:
        c = getattr(gen, k)()
        c.elms = [e for e in c.elms if e[0] != 'x']
        for t, a in c.elms:                       # ammeters show "A" instead of a reading
            if t == 'Ammeter': a.update(f=2, me=99)
        c.names, c.scopes, c.adjs = {}, [], []
        pg = browser().new_page(); pg.goto(url(c.xml()))
        pg.wait_for_function("window.CircuitJS1 !== undefined", timeout=60000)
        time.sleep(1.5); pg.evaluate("CircuitJS1.setSimRunning(false)")
        # menu entries carry a check mark in front of the text, the Options entry holds its whole submenu
        menu = lambda t: pg.locator("td.gwt-MenuItem, li.menuItem").filter(has_text=re.compile(t + "$")).locator("visible=true").first.click()
        opts = lambda: pg.locator("td.gwt-MenuItem").filter(has_text=re.compile("^Options")).first.click()
        opts(); menu("White Background")
        opts(); menu("Show Voltage")
        pg.evaluate("window.svgout=null; CircuitJS1.onsvgrendered=function(s,svg){window.svgout=svg}; CircuitJS1.getCircuitAsSVG()")
        pg.wait_for_function("window.svgout !== null", timeout=30000)
        svg = pg.evaluate("svgout")
        w, h = map(int, re.search(r'width="(\d+)" height="(\d+)"', svg).groups())
        p2 = browser().new_page(); p2.set_content(f'<html><body style="margin:0">{svg}</body></html>')
        out = os.path.join(LECTURE, "figures", "falstad", f"{k}_schematic.pdf")
        p2.pdf(path=out, width=f"{w}px", height=f"{h+2}px", print_background=True, page_ranges="1")
        pg.close(); p2.close(); print(out)

def setp(circ, name, **kw): circ.elms[circ.names[name]][1].update(kw)
def edge(t, v, lo, hi, rising=True, after=0):
    """time from crossing lo to crossing hi (rising) after time 'after'"""
    m = t >= after; t, v = t[m], v[m]
    if rising:
        i0 = np.argmax(v > lo); i1 = i0 + np.argmax(v[i0:] > hi)
    else:
        i0 = np.argmax(v < hi); i1 = i0 + np.argmax(v[i0:] < lo)
    return t[i1] - t[i0]
def window(r, t0, t1): return r[(r[:,0] >= t0) & (r[:,0] < t1)]
def avg(r, col, t0, t1):
    w = window(r, t0, t1); t = w[:,0]; return np.trapezoid(w[:,col], t) / (t[-1]-t[0])
V = 3.3
which = sys.argv[1:] or list(gen.CIRCUITS)
if "figures" in which:              # "figures" alone: all schematics; "figures H I": only these
    figures(which[which.index("figures")+1:] or gen.CIRCUITS); which = which[:which.index("figures")]
if 'A' in which:
    for p in (1, 0):
        c = gen.A(); setp(c, 'in', p=p)
        r = run(c.xml(), 4.1e-3, ['PIN'], [c.names['amm']])
        pts = "  ".join(f"{r[k,1]:.2f}V:{r[k,2]*1e3:.1f}mA" for k in (np.argmin(abs(r[:,1]-v)) for v in (0, 0.13, 0.4, 2.62, 2.9, 3.3, 3.7)))
        print(f"A output {'H' if p else 'L'}: {pts}", flush=True)
if 'B' in which:
    for cl, sl in [(1e-11, 2), (1e-10, 2), (1e-9, 2), (1e-12, 2), (1e-12, 0.02), (1e-10, 0.02)]:
        c = gen.B(); setp(c, 'cl', c=cl); setp(c, 'drv', sl=sl)
        r = run(c.xml(), 3.05e-6, ['PIN', 'G'], [c.names['isup']])
        t, pin = r[:,0], r[:,1]
        tr = edge(t, pin, 0.33, 2.97, True, 1e-6); tf = edge(t, pin, 0.33, 2.97, False, 1.5e-6)
        Iavg = avg(r, 3, 1e-6, 3e-6); Ipk = window(r, 1e-6, 3e-6)[:,3].max()
        print(f"B C_L={cl:.0e} slew={sl}: tr={tr*1e9:.2f} ns tf={tf*1e9:.2f} ns I_avg={Iavg*1e6:.1f} uA (C V f={cl*V*1e6*1e6:.1f} uA) Ipk={Ipk*1e3:.1f} mA", flush=True)
if 'C' in which:
    c = gen.C(); r = run(c.xml(), 2e-6, ['PIN_A', 'PIN_B'], [c.names['amm']])
    print(f"C contention: I={r[-1,3]*1e3:.2f} mA V_line={r[-1,1]:.3f} V  P_PA={(V-r[-1,1])*r[-1,3]*1e3:.1f} mW P_NB={r[-1,1]*r[-1,3]*1e3:.1f} mW", flush=True)
if 'D' in which:
    for rp, cb, in2 in [(4700, 2e-10, 1), (1800, 2e-10, 1), (5900, 2e-10, 1), (1000, 2e-10, 1), (470, 2e-10, 1), (220, 2e-10, 1), (4700, 4e-10, 1), (4700, 2e-10, 0)]:
        c = gen.D(); setp(c, 'rp', r=rp); setp(c, 'cb', c=cb); setp(c, 'cpp', c=cb); setp(c, 'in2', p=in2)
        r = run(c.xml(), 2.2e-5, ['BUS', 'PP'], [c.names['rp']])
        t = r[:,0]
        tr = edge(t, r[:,1], 0.99, 2.31, True, 1e-5); tf = edge(t, r[:,1], 0.99, 2.31, False, 1.5e-5)
        trpp = edge(t, r[:,2], 0.99, 2.31, True, 1e-5)
        vol = window(r, 1.9e-5, 2e-5)[:,1].mean(); vmax = window(r, 1.4e-5, 1.5e-5)[:,1].mean()
        print(f"D R_P={rp} C={cb:.0e} in2={in2}: tr(30-70)={tr*1e9:.0f} ns (0.8473RC={0.8473*rp*cb*1e9:.0f}) tf={tf*1e9:.1f} ns tr_pp={trpp*1e9:.1f} ns V_OL={vol*1e3:.0f} mV V_high={vmax:.3f} I_low={window(r,1.9e-5,2e-5)[:,3].mean()*1e3:.2f} mA", flush=True)
if 'E' in which:
    for rpu, rmcu in [(4700, 33000), (1000, 33000), (1000, 3300), (470, 33000)]:
        c = gen.E(); setp(c, 'rpu1', r=rpu); setp(c, 'rpu2', r=rpu); setp(c, 'rmcu', r=rmcu)
        r = run(c.xml(), 1.2e-2, ['PIN1', 'PIN2', 'VDD'], [c.names['inj']], every=20)
        w = window(r, 1.15e-2, 1.2e-2)
        print(f"E R_PU={rpu} R_MCU={rmcu}: PIN1 max={w[:,1].max():.3f} PIN2 max={w[:,2].max():.3f} VDD={w[:,3].mean():.3f} (min {w[:,3].min():.3f}) I_inj max={w[:,4].max()*1e3:.3f} mA, I_mcu={w[:,3].mean()/rmcu*1e3:.3f} mA", flush=True)
if 'F' in which:
    for name, sel, fly, byp, rb in [("coil, none", 0, 1, 0, 1000), ("coil, diode", 0, 0, 0, 1000), ("coil, diode+zener", 0, 0, 1, 1000),
                                     ("coil, none, RB=47k", 0, 1, 0, 47000), ("lamp, RB=1k", 1, 1, 0, 1000), ("lamp, RB=330", 1, 1, 0, 330)]:
        c = gen.F(); setp(c, 'sel', p=sel); setp(c, 'flyback', p=fly); setp(c, 'bypass', p=byp); setp(c, 'rb', r=rb)
        r = run(c.xml(), 1.01e-2, ['C'], [c.names['icoil'], c.names['lamp'], c.names['rb']])
        t = r[:,0]; w = window(r, 5e-3, 1.0e-2)          # one period, switch-off at 7.5 ms
        on = window(r, 7e-3, 7.4e-3)
        ic = on[:,2] if sel == 0 else on[:,3]
        print(f"F {name}: V_C max={w[:,1].max():.1f} V min={w[:,1].min():.2f} V; on: I_C={abs(ic).mean()*1e3:.1f} mA V_CE={on[:,1].mean():.3f} V I_B={on[:,4].mean()*1e3:.2f} mA P_Q={on[:,1].mean()*abs(ic).mean()*1e3:.0f} mW", flush=True)
        if sel == 0:
            off = window(r, 7.5e-3, 1.0e-2); i0 = abs(on[:,2]).mean()
            k = np.argmax(np.abs(off[:,2]) < 0.1*i0); print(f"   coil current falls to 10% after {(off[k,0]-7.5e-3)*1e6:.0f} us", flush=True)
if 'G' in which:
    for rs, sl in [(0.1, 5), (10, 5), (20, 5), (35, 5), (50, 5), (0.1, 0.3)]:
        c = gen.G(); setp(c, 'rs', r=rs); setp(c, 'drv', sl=sl)
        r = run(c.xml(), 1.2e-7, ['PIN', 'RX'], [c.names['desd'], c.names['desd2']])
        w = window(r, 4e-8, 1.2e-7)
        print(f"G R_S={rs} slew={sl}: RX max={w[:,2].max():.2f} min={w[:,2].min():.2f}  PIN max={w[:,1].max():.2f} min={w[:,1].min():.2f}  I_esd max={w[:,3].max()*1e3:.1f}/{w[:,4].max()*1e3:.1f} mA", flush=True)
if 'H' in which:
    for rp, cb, f, in2 in [(1200, 2.5e-10, 4e5, 1), (1500, 2.5e-10, 4e5, 1), (4700, 2.5e-10, 4e5, 1),
                           (4700, 2.5e-10, 1e5, 1), (1800, 2.5e-10, 1e5, 1), (1200, 2.5e-10, 4e5, 0)]:
        c = gen.H(); setp(c, 'rp', r=rp); setp(c, 'cb', c=cb); setp(c, 'clk', fr=f); setp(c, 'in2', p=in2)
        T = 1/f; r = run(c.xml(), 2.05*T, ['SDA_5V', 'SDA_3V3'], [c.names['rp']], every=2)
        t = r[:,0]
        tr = edge(t, r[:,1], 1.5, 3.5, True, 0.8*T); tf = edge(t, r[:,1], 1.5, 3.5, False, 1.2*T)
        tr3 = edge(t, r[:,2], 0.99, 2.31, True, 0.8*T)
        lo, hi = window(r, 1.84*T, 1.96*T), window(r, 1.36*T, 1.48*T)
        print(f"H R_P={rp} C={cb:.0e} f={f:.0e} sensor={'released' if in2 else 'low'}: tr5(30-70)={tr*1e9:.0f} ns (0.8473RC={0.8473*rp*cb*1e9:.0f})"
              f" tf5={tf*1e9:.1f} ns tr3={tr3*1e9:.0f} ns  low: 5V={lo[:,1].mean()*1e3:.0f} mV 3V3={lo[:,2].mean()*1e3:.0f} mV I={lo[:,3].mean()*1e3:.2f} mA"
              f"  high: 5V={hi[:,1].mean():.2f} 3V3={hi[:,2].mean():.2f} V", flush=True)
if 'I' in which:
    for name, fly, byp, L in [("diode", 0, 0, 0.3), ("diode+zener", 0, 1, 0.3), ("none", 1, 0, 0.3), ("diode, L=1H", 0, 0, 1.0)]:
        c = gen.I(); setp(c, 'flyback', p=fly); setp(c, 'bypass', p=byp); setp(c, 'coil', l=L)
        r = run(c.xml(), 0.06, ['D'], [c.names['icoil'], c.names['q']], every=5)
        on = window(r, 0.045, 0.0495); off = window(r, 0.05, 0.06)
        i0 = abs(on[:,2]).mean(); k = np.argmax(np.abs(off[:,2]) < 0.1*i0)
        print(f"I {name}: on: I={i0*1e3:.1f} mA V_DS={on[:,1].mean()*1e3:.1f} mV; off: V_D max={off[:,1].max():.1f} V,"
              f" current < 10 % after {(off[k,0]-0.05)*1e3:.2f} ms", flush=True)
if 'J' in which:
    for rs, sl in [(33, 0.5), (0.1, 0.5), (0.1, 5), (33, 5), (15, 0.5)]:
        c = gen.J(); setp(c, 'rs', r=rs); setp(c, 'drv', sl=sl)
        r = run(c.xml(), 1.2e-7, ['PIN', 'RX'], [c.names['desd'], c.names['desd2']])
        w = window(r, 4e-8, 1.2e-7); t = r[:,0]
        tr = edge(t, r[:,2], 0.33, 2.97, True, 9e-8)
        print(f"J R_S={rs} slew={sl}: RX max={w[:,2].max():.2f} min={w[:,2].min():.2f} tr(10-90)={tr*1e9:.1f} ns"
              f"  I_esd max={w[:,3].max()*1e3:.1f}/{w[:,4].max()*1e3:.1f} mA", flush=True)
    for rs, sl in [(0.1, 5), (33, 5), (33, 0.5)]:      # fastest drive setting (models of part G) on the same trace
        c = gen.G(); setp(c, 'tl', de=6.7e-10); setp(c, 'rs', r=rs); setp(c, 'drv', sl=sl)
        r = run(c.xml(), 1.2e-7, ['PIN', 'RX'], [c.names['desd'], c.names['desd2']])
        w = window(r, 4e-8, 1.2e-7); t = r[:,0]
        tr = edge(t, r[:,2], 0.33, 2.97, True, 9e-8)
        print(f"J fast drive R_S={rs} slew={sl}: RX max={w[:,2].max():.2f} min={w[:,2].min():.2f} tr(10-90)={tr*1e9:.1f} ns"
              f"  I_esd max={w[:,3].max()*1e3:.1f}/{w[:,4].max()*1e3:.1f} mA", flush=True)
