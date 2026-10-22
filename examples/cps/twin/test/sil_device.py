#!/usr/bin/env python3
"""Software-in-the-loop test of the twin server: the tank and the device
controller in Python, talking to the server like the ESP32 does.

Usage: sil_device.py [--url wss://127.0.0.1:8443] [--leak-at 40] [--duration 90] [--fast]

--fast sends the samples without waiting (device time still advances by
0.5 s per sample), so a 90 s run takes a second. The script prints what the
server answers and fails if the leak alarm does not come.
"""
import argparse
import asyncio
import json
import math
import random
import ssl
from pathlib import Path

import aiohttp

# the same numbers as chips/tank.chip.c and twin.ino
AREA, Q_PUMP, K_OUT, K_LEAK = 0.04, 2e-3, 2e-3, 1.5e-3
KP, KI, VALVE, LEAK = 10, 0.2, 0.5, 0.5


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="wss://127.0.0.1:8443")
    p.add_argument("--id", default="sil")
    p.add_argument("--token", default="ec-lecture-2026")
    p.add_argument("--leak-at", type=float, default=40)
    p.add_argument("--duration", type=float, default=90)
    p.add_argument("--fast", action="store_true")
    a = p.parse_args()

    tls = ssl.create_default_context(cafile=Path(__file__).parent.parent / "server/ca.crt")
    tls.check_hostname = "127.0.0.1" not in a.url    # the certificate names the public address
    h, integral, sp, alarm_at = 0.1, 0.0, 0.5, None
    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(f"{a.url}/device?id={a.id}", ssl=tls, protocols=("twin",),
                                      headers={"Authorization": f"Bearer {a.token}"}) as ws:
            for k in range(int(a.duration * 10)):              # 100 ms control steps
                t = k / 10
                leak = LEAK if t >= a.leak_at else 0
                q = VALVE * K_OUT * math.sqrt(h)
                hm = h + random.randint(-2, 2) * 1e-3
                e = sp - hm
                u = q / Q_PUMP + KP * e + integral
                if 0 < u < 1:
                    integral += KI * e * 0.1
                u = min(max(u, 0), 1)
                if k % 5 == 4:                                 # telemetry every 500 ms
                    await ws.send_str(json.dumps({"t": int(t * 1000), "h": round(hm, 3),
                                                  "q": round(q * 1e6), "u": round(u, 3), "sp": sp}))
                    reply = json.loads((await ws.receive()).data)
                    sp = reply["sp"]
                    if reply["alarm"] and alarm_at is None:
                        alarm_at = t
                        print(f"t={t:5.1f} s  ALARM, leak estimate {reply['leak']:.2f} L/s, setpoint -> {sp} m")
                    if k % 50 == 49:
                        print(f"t={t:5.1f} s  h={hm:.3f} m  u={u:.2f}  leak estimate {reply['leak']:.2f} L/s")
                    if not a.fast:
                        await asyncio.sleep(0.5)
                for _ in range(10):                            # the tank, 10 ms steps
                    h += 0.01 * (Q_PUMP * u - q - leak * K_LEAK * math.sqrt(h)) / AREA
    if alarm_at is None:
        raise SystemExit("FAIL: no leak alarm")
    print(f"OK: leak at {a.leak_at} s, alarm after {alarm_at - a.leak_at:.1f} s")


asyncio.run(main())
