# Digital twin of a water tank

Example for the chapter "Cyber-Physical Systems" (section "Case Study: a
Digital Twin"). The **physical part** runs in Wokwi: an ESP32-C3 keeps the
level of a water tank, and the tank itself is a custom chip that models the
physics (pump, consumer valve, leak). The **cyber part** runs on the lecture
server: a Python program keeps a model of every connected tank, fed with the
same data as the real one. Device and server talk over a secure WebSocket
(TLS, our own certificate authority).

```
 Wokwi (simulated)                           server srv2003097.hstgr.cloud:8443
 ┌───────────────┐  I2C   ┌─────────────┐    ┌───────────────────────────────┐
 │ ESP32-C3      │◄──────►│ tank chip   │    │ twin.py (aiohttp)             │
 │  control task │  PWM   │ A dh/dt =   │    │  per device: observer         │
 │  PI + trip    ├───────►│ Q u - q_out │    │   -> estimated leak flow      │
 │  (100 ms)     │        │   - q_leak  │    │  supervisor: leak -> alarm,   │
 │               │        └─────────────┘    │   safe setpoint               │
 │  network      │  wss:// (TLS 1.2+, CA     │  /ui -> dashboard.html        │
 │  (loop)       │◄─────── pinning, token) ──►  operator key for commands   │
 └───────────────┘   telemetry 2/s, commands └──────────────┬────────────────┘
   ONLINE + ALARM LEDs                                      │ wss://
                                                         browser (dashboard)
```

| File | Content |
|---|---|
| `twin.ino` | device: control task (PI, feedforward, high-level trip), WebSocket client with TLS |
| `chips/tank.chip.{c,json}` | tank model, level sensor + outlet flow meter on I2C 0x28, controls "valve" and "leak" |
| `diagram.json`, `libraries.txt`, `wokwi.toml` | Wokwi project (library "WebSockets") |
| `server/twin.py` | twin server: observer, leak alarm, operator commands, CSV log |
| `server/dashboard.html` | live dashboard (plain JavaScript, no libraries) |
| `server/run.sh` | `start`, `stop`, `status`, `key` (prints the operator key) |
| `server/make_pki.sh`, `server/ca.crt` | creates the CA and the server certificate; `ca.crt` is public and compiled into the firmware |
| `test/leak.yaml` | scenario: leak after 30 s, more consumption 20 s after the alarm |
| `test/sil_device.py` | software-in-the-loop: tank + controller in Python, to test the server without Wokwi |
| `test/figures.py` | the figure of the lecture from a scenario run |

## In the lecture: checklist

1. **Start the server** (it does not start by itself after a reboot of the server):
   ```sh
   ssh srv2003097.hstgr.cloud
   /home/shared/embeddedcomputing/Lecture/examples/cps/twin/server/run.sh status   # running?
   /home/shared/embeddedcomputing/Lecture/examples/cps/twin/server/run.sh start
   /home/shared/embeddedcomputing/Lecture/examples/cps/twin/server/run.sh key      # operator key
   ```
2. **Open the dashboard**: <https://srv2003097.hstgr.cloud:8443/>. The browser
   warns because it does not know our CA. Either accept once ("Advanced" →
   "Proceed"), or import `server/ca.crt` as a trusted authority in the browser
   (Settings → Certificates → Authorities → Import) -- then the warning is
   gone for good. Paste the operator key into the field at the bottom (the
   browser remembers it).
3. **Open the Wokwi project.** The first time: open
   <https://wokwi.com/projects/new/esp32-c3>, replace `sketch.ino` with
   `twin.ino` and `diagram.json`, add `libraries.txt`, create a custom chip
   named `tank` ("New file…" → "Custom chip (C)") and paste
   `chips/tank.chip.c` and `chips/tank.chip.json`. Save the project and keep
   the link for the next lecture.
4. **Start the simulation.** After about 5 s the green ONLINE LED is on and
   the device `tank1` appears on the dashboard.
5. **Demo**, step by step:
   * dashboard: change the setpoint (slider + "Send setpoint"): the device follows
   * Wokwi: click the tank chip, move "Consumer valve" -- outlet flow changes,
     the controller compensates, the twin stays quiet (the flow is measured)
   * Wokwi: move "Leak" to 0.5 -- the tank frame turns red; after about 5 s
     the twin estimates ~0.5 L/s, raises the alarm (red LED, red tag on the
     dashboard) and lowers the setpoint to 250 mm
   * the orange curve (the model without measurements) drifts away from
     the real level: this is why a twin needs live data
   * "Leak" back to 0, then "Acknowledge alarm" on the dashboard: back to normal
   * stop the server (`run.sh stop`): the ONLINE LED goes off after 5 s, but
     the tank keeps its level -- the control loop runs on the device.
     `run.sh start` again: the device reconnects by itself within seconds.
6. **Students** can run the same project: each changes `DEVICE` in the
   sketch to an own name and gets an own twin on the dashboard. Only the
   holder of the operator key can send commands.

## Run locally

```sh
arduino-cli lib install WebSockets
arduino-cli compile -b esp32:esp32:esp32c3 --output-dir build .
wokwi-cli chip compile chips/tank.chip.c -o chips/tank.chip.wasm
wokwi-cli --scenario test/leak.yaml --timeout 150000 --serial-log-file device.csv . > device.log
python3 test/figures.py <dir with device.log and tank1.csv> ../../../figures
```

The serial output is CSV: `t_ms,h_mm,q_mls,u,sp_mm,online,alarm`, with
comment lines starting with `#` (connected, alarm on/off).

Server without Wokwi (Python with `aiohttp`):

```sh
server/run.sh start                                          # or: python3 server/twin.py --host 127.0.0.1
python3 test/sil_device.py --url wss://srv2003097.hstgr.cloud:8443 --fast
```

## Server setup (done once)

* Python venv with `aiohttp`: `~/.local/share/lecture-tools/venv`
* Certificates, operator key, logs: `~/.local/share/lecture-tools/cps-twin/`
  (outside the repository, the `.key` files are secret). Created with
  `server/make_pki.sh ~/.local/share/lecture-tools/cps-twin 186.240.158.241 srv2003097.hstgr.cloud`.
  The server certificate is valid for 825 days (until January 2029); run
  the same command again to renew it -- the CA stays, so the firmware needs
  no change. A new CA would need a new `CA_CERT` in `twin.ino`.
* Port 8443 must be reachable from the internet (Wokwi's simulated Wi-Fi
  connects from Google Cloud addresses).

## Security, and what a real product would do differently

* **TLS with CA pinning**: the device accepts only server certificates signed
  by our own CA. Without it, anybody between Wokwi and the server could read
  and change the commands.
* **Device token**: the server accepts only devices that send the token. The
  token is in the public sketch, so here it only keeps out accidental
  clients. A product gives every device its own secret (provisioning) or its
  own client certificate (mutual TLS).
* **Operator key** for commands from the dashboard; viewing is open.
* The device stays safe without the server: the high-level trip and the
  control loop never wait for the network.

Tested 2026-10-22: `wokwi-cli` scenario `test/leak.yaml` against the public
server (leak at 40.0 s, alarm at 44.4 s, safe setpoint reached, no false
alarm when the consumer valve opens), `test/sil_device.py` locally and over
the internet, dashboard in headless Chromium (Playwright).
