#!/usr/bin/env python3
"""Digital twin server for the water tank (cyber part of the CPS example).

Devices connect to wss://<host>:8443/device?id=<name> with the header
"Authorization: Bearer <device token>" and send their measurements twice a
second. For every device the server keeps a twin: a model of the tank fed
with the same pump command and outlet flow as the real one. The twin

  * follows the measured level with an observer and estimates the leak flow,
    a quantity that no sensor on the device measures (a "virtual sensor"),
  * runs the plain model without measurements next to it, to show how far
    model and reality drift apart,
  * acts as supervisor: on a leak it lowers the setpoint and switches the
    alarm on; the operator sets the setpoint and acknowledges the alarm.

Browsers open https://<host>:8443/ (dashboard.html) and get live data over
the WebSocket /ui. Commands from the browser need the operator key.

Usage: twin.py [--dir ~/.local/share/lecture-tools/cps-twin] [--host 0.0.0.0] [--port 8443]
The directory holds server.crt/server.key (make_pki.sh), operator.key (created
on the first start) and the CSV logs.
"""
import argparse
import hmac
import json
import re
import secrets
import ssl
import time
from pathlib import Path

from aiohttp import WSMsgType, web

# Tank parameters as the twin knows them (the same as in chips/tank.chip.c)
AREA = 0.04          # m^2
Q_PUMP = 2.0e-3      # m^3/s at full speed
# Observer gains (tuned offline: leak noise ~0.015 L/s, 90 % after ~5 s)
L1, L2 = 0.3, 0.004
LEAK_LIMIT = 0.15e-3     # m^3/s: above this for LEAK_TIME seconds = leak alarm
LEAK_TIME = 3.0
SAFE_SETPOINT = 0.25     # m: less pressure, less leak flow until repaired
HISTORY = 600            # samples kept per device for new browsers (5 min)
MAX_DEVICES = 50

DEVICE_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


class Twin:
    """Model of one tank, updated with every telemetry message."""

    def __init__(self, name):
        self.name = name
        self.t = None              # device time of the last sample in s
        self.h_twin = 0.0          # observer: level, corrected by measurements
        self.leak = 0.0            # observer: estimated leak flow in m^3/s
        self.h_model = 0.0         # plain model, never corrected
        self.leak_since = None
        self.setpoint = 0.5        # operator setpoint in m
        self.alarm = False
        self.history = []

    def command(self):
        """What the device should do now."""
        sp = SAFE_SETPOINT if self.alarm else self.setpoint
        return {"sp": round(sp, 3), "alarm": int(self.alarm), "leak": round(self.leak * 1e3, 3)}

    def update(self, t, h, q, u):
        """One step with device time t (s), level h (m), outlet flow q (m^3/s), pump u (0..1)."""
        dt = None if self.t is None else t - self.t
        self.t = t
        if dt is None or not 0 < dt < 2:       # first sample or a gap: start again from the measurement
            self.h_twin = self.h_model = h
            self.leak = 0.0
            self.leak_since = None
            return
        inflow = Q_PUMP * u
        # observer: predict with the model, then correct with the measured level
        predicted = self.h_twin + dt * (inflow - q - self.leak) / AREA
        residual = h - predicted
        self.h_twin = predicted + L1 * residual
        self.leak = max(0.0, self.leak - L2 * residual)   # level lower than predicted -> water missing
        # the same model without measurements
        self.h_model = min(max(self.h_model + dt * (inflow - q) / AREA, 0.0), 1.0)

        # supervisor: a leak that lasts LEAK_TIME seconds raises the alarm
        if self.leak > LEAK_LIMIT:
            self.leak_since = self.leak_since if self.leak_since is not None else t
            if t - self.leak_since >= LEAK_TIME:
                self.alarm = True
        else:
            self.leak_since = None

    def reset(self):
        self.alarm = False
        self.leak_since = None
        self.h_model = self.h_twin


class Server:
    def __init__(self, directory, device_token):
        self.dir = directory
        self.device_token = device_token
        key_file = directory / "operator.key"
        if not key_file.exists():
            key_file.write_text(secrets.token_urlsafe(12) + "\n")
            key_file.chmod(0o600)
        self.operator_key = key_file.read_text().strip()
        (directory / "log").mkdir(exist_ok=True)
        self.twins = {}            # name -> Twin
        self.devices = {}          # name -> WebSocket of the connected device
        self.browsers = set()

    async def broadcast(self, message):
        text = json.dumps(message)
        for ws in list(self.browsers):
            try:
                await ws.send_str(text)
            except ConnectionError:
                self.browsers.discard(ws)

    def log(self, twin, sample):
        path = self.dir / "log" / f"{twin.name}.csv"
        new = not path.exists()
        with path.open("a") as f:
            if new:
                f.write("time,t,h,q,u,sp,h_twin,h_model,leak,alarm\n")
            f.write(f"{time.time():.1f},{sample['t']:.1f},{sample['h']:.3f},{sample['q']:.3f},"
                    f"{sample['u']:.3f},{sample['sp']:.3f},{sample['h_twin']:.3f},"
                    f"{sample['h_model']:.3f},{sample['leak']:.3f},{sample['alarm']}\n")

    # --- devices ---------------------------------------------------------
    async def device(self, request):
        name = request.query.get("id", "")
        auth = request.headers.get("Authorization", "")
        if not hmac.compare_digest(auth.encode(), f"Bearer {self.device_token}".encode()):
            raise web.HTTPUnauthorized(text="wrong device token\n")
        if not DEVICE_ID.match(name):
            raise web.HTTPBadRequest(text="id: 1..32 letters, digits, - or _\n")
        if name not in self.twins and len(self.twins) >= MAX_DEVICES:
            raise web.HTTPServiceUnavailable(text="too many devices\n")

        ws = web.WebSocketResponse(protocols=("twin",), heartbeat=10, max_msg_size=1024)
        await ws.prepare(request)
        old = self.devices.get(name)
        if old is not None:
            await old.close()        # the same name connects again: newest wins
        self.devices[name] = ws
        twin = self.twins.setdefault(name, Twin(name))
        twin.t = None
        twin.history = []            # a restarted device counts its time from 0 again
        print(f"device {name} connected from {request.remote}", flush=True)
        await self.broadcast({"type": "connected", "id": name})
        await ws.send_str(json.dumps(twin.command()))
        try:
            async for msg in ws:
                if msg.type != WSMsgType.TEXT:
                    continue
                try:
                    data = json.loads(msg.data)
                    t, h, q, u = data["t"] / 1000, float(data["h"]), float(data["q"]) * 1e-6, float(data["u"])
                    sp = float(data.get("sp", 0))
                except (ValueError, KeyError, TypeError):
                    continue
                twin.update(t, h, q, u)
                await ws.send_str(json.dumps(twin.command()))   # also the heartbeat for the device
                sample = {"type": "sample", "id": name, "t": t, "h": h, "q": q * 1e3, "u": u, "sp": sp,
                          "h_twin": twin.h_twin, "h_model": twin.h_model, "leak": twin.leak * 1e3,
                          "alarm": int(twin.alarm), "setpoint": twin.setpoint}
                twin.history = (twin.history + [sample])[-HISTORY:]
                self.log(twin, sample)
                await self.broadcast(sample)
        finally:
            if self.devices.get(name) is ws:
                del self.devices[name]
                await self.broadcast({"type": "offline", "id": name})
            print(f"device {name} disconnected", flush=True)
        return ws

    # --- browsers --------------------------------------------------------
    async def ui(self, request):
        ws = web.WebSocketResponse(heartbeat=30, max_msg_size=1024)
        await ws.prepare(request)
        await ws.send_str(json.dumps({
            "type": "hello",
            "devices": {n: {"online": n in self.devices, "history": tw.history} for n, tw in self.twins.items()},
        }))
        self.browsers.add(ws)
        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.browser_command(ws, msg.data)
        finally:
            self.browsers.discard(ws)
        return ws

    async def browser_command(self, ws, text):
        try:
            data = json.loads(text)
            twin = self.twins[data["id"]]
        except (ValueError, KeyError, TypeError):
            return
        if not hmac.compare_digest(str(data.get("key", "")).encode(), self.operator_key.encode()):
            await ws.send_str(json.dumps({"type": "error", "text": "wrong operator key"}))
            return
        if "sp" in data:
            twin.setpoint = min(max(float(data["sp"]), 0.1), 0.9)
        if data.get("reset"):
            twin.reset()
        if data["id"] in self.devices:
            await self.devices[data["id"]].send_str(json.dumps(twin.command()))
        print(f"operator: {data['id']} setpoint {twin.setpoint:.2f} m, alarm {twin.alarm}", flush=True)

    async def index(self, request):
        return web.FileResponse(Path(__file__).with_name("dashboard.html"))


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--dir", type=Path, default=Path.home() / ".local/share/lecture-tools/cps-twin")
    parser.add_argument("--host", default="0.0.0.0", help="127.0.0.1 = reachable only from this machine")
    parser.add_argument("--port", type=int, default=8443)
    parser.add_argument("--device-token", default="ec-lecture-2026")
    args = parser.parse_args()

    server = Server(args.dir, args.device_token)
    app = web.Application()
    app.router.add_get("/", server.index)
    app.router.add_get("/device", server.device)
    app.router.add_get("/ui", server.ui)

    tls = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    tls.minimum_version = ssl.TLSVersion.TLSv1_2
    tls.load_cert_chain(args.dir / "server.crt", args.dir / "server.key")
    print(f"operator key: {server.operator_key}", flush=True)
    web.run_app(app, host=args.host, port=args.port, ssl_context=tls, shutdown_timeout=2,
                print=lambda s: print(s, flush=True))


if __name__ == "__main__":
    main()
