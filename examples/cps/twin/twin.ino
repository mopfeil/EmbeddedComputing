// Digital twin, device side: the ESP32-C3 keeps the level of a water tank and
// reports to a twin server over a secure WebSocket (TLS). The server runs a
// model of the tank, estimates leaks that no sensor sees, and sends back the
// setpoint and the alarm state. The tank is a custom chip (chips/tank.chip.c).
//
//   I2C  (SDA 8, SCL 9)  tank sensors 0x28: reg 0 level in mm, reg 1 outlet flow in mL/s
//   PWM  GPIO6 pump
//   GPIO4 ONLINE LED, GPIO10 ALARM LED
//
// The control loop runs in its own FreeRTOS task and never waits for the
// network: a slow TLS handshake or a lost connection must not stop the pump
// control. Commands come in through a queue, telemetry goes out through a
// mailbox (queue of length 1).
//
// Wokwi: add the library "WebSockets" (libraries.txt) and the custom chip.
//
// In the lecture (details in README.md):
//   1. on the server: examples/cps/twin/server/run.sh start   (run.sh key = operator key)
//   2. dashboard: https://srv2003097.hstgr.cloud:8443/  (accept the certificate warning
//      or import server/ca.crt), paste the operator key
//   3. start the simulation: ONLINE LED on after ~5 s, "tank1" on the dashboard
//   4. click the tank chip: "Leak" 0.5 -> alarm after ~5 s, setpoint 250 mm;
//      "Consumer valve" -> no alarm; "Acknowledge alarm" on the dashboard

#include <WiFi.h>
#include <Wire.h>
#include <WebSocketsClient.h>

const char *HOST = "srv2003097.hstgr.cloud";    // the twin server
const uint16_t PORT = 8443;
const char *DEVICE = "tank1";                    // <- change me, one twin per name
const char *TOKEN = "ec-lecture-2026";           // device token, sent as HTTP header

// The certificate of our own CA (server/ca.crt). The device accepts only a
// server certificate signed by this CA -- no other server can pretend to be
// the twin, even with a certificate from a public CA.
const char *CA_CERT = R"(-----BEGIN CERTIFICATE-----
MIIB3zCCAYagAwIBAgIUGvxo7no1ov/HoARhayx7NHtAbGUwCgYIKoZIzj0EAwIw
PDEjMCEGA1UECgwaRW1iZWRkZWQgQ29tcHV0aW5nIGxlY3R1cmUxFTATBgNVBAMM
DFR3aW4gZGVtbyBDQTAeFw0yNjEwMjIxMjM1MTdaFw0zNjEwMTkxMjM1MTdaMDwx
IzAhBgNVBAoMGkVtYmVkZGVkIENvbXB1dGluZyBsZWN0dXJlMRUwEwYDVQQDDAxU
d2luIGRlbW8gQ0EwWTATBgcqhkjOPQIBBggqhkjOPQMBBwNCAARrqICjIsSzvNgX
PABvtyT9BizTUvvZBcZwVssxP/5V3qLLYPoOQgIuzDHwIkgVpGCu2OPcwj5lKPCN
fjy8ynbzo2YwZDAdBgNVHQ4EFgQUb51ThmCUSCeafHt7FbnfaShwdK4wHwYDVR0j
BBgwFoAUb51ThmCUSCeafHt7FbnfaShwdK4wEgYDVR0TAQH/BAgwBgEB/wIBADAO
BgNVHQ8BAf8EBAMCAQYwCgYIKoZIzj0EAwIDRwAwRAIgJpuzVfdlL2xVgLnO098C
ICcJ1b//8+IR9kXeVfn7GOUCIEL/n2ImJmOsh5Q3SrFQ9uxHJHM8nLrCXTCoCaiU
83um
-----END CERTIFICATE-----
)";

const int PIN_SDA = 8, PIN_SCL = 9, PIN_PUMP = 6, PIN_ONLINE = 4, PIN_ALARM = 10;
const uint8_t TANK = 0x28;
const float Q_PUMP = 2000;            // pump flow at full speed in mL/s
const float KP = 10, KI = 0.2;        // PI controller on the level (m), output 0..1
const float H_TRIP = 0.95;            // local high-level trip in m, works without network
const uint32_t LINK_TIMEOUT = 5000;   // ms without a message from the server = offline

struct Command { float setpoint; int alarm; };        // network -> control (-1 = unchanged)
struct Telemetry { uint32_t t; float h, q, u, sp; };  // control -> network

QueueHandle_t commands;
QueueHandle_t telemetryBox;          // length 1: always the newest values
WebSocketsClient ws;
volatile uint32_t lastHeard;         // millis() of the last server message

// Reads one 16-bit register of the tank chip
bool readRegister(uint8_t reg, uint16_t *value) {
  Wire.beginTransmission(TANK);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0 || Wire.requestFrom(TANK, (uint8_t)2) != 2) return false;
  *value = Wire.read() << 8 | Wire.read();
  return true;
}

void controlTask(void *param) {
  float setpoint = 0.5, integral = 0, sumU = 0, sumQ = 0;
  int n = 0;
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    Command cmd;
    while (xQueueReceive(commands, &cmd, 0) == pdTRUE) {
      if (cmd.setpoint >= 0) setpoint = constrain(cmd.setpoint, 0.1, 0.9);
      if (cmd.alarm >= 0 && cmd.alarm != digitalRead(PIN_ALARM)) {
        digitalWrite(PIN_ALARM, cmd.alarm);
        Serial.printf("# alarm %s, setpoint %.0f mm\n", cmd.alarm ? "on" : "off", setpoint * 1000);
      }
    }

    uint16_t rawH, rawQ;
    if (readRegister(0, &rawH) && readRegister(1, &rawQ)) {
      float h = rawH / 1000.0, q = rawQ;                   // m, mL/s
      float e = setpoint - h;
      float feedforward = q / Q_PUMP;                       // replace what the consumer takes
      float u = feedforward + KP * e + integral;
      if (u > 0 && u < 1) integral += KI * e * 0.1;         // anti-windup: integrate only unsaturated
      u = constrain(u, 0, 1);
      if (h > H_TRIP) u = 0;                                // safety does not depend on the server
      ledcWrite(PIN_PUMP, u * 1023);

      sumU += u; sumQ += q;
      if (++n == 5) {                                       // every 500 ms: averages to the twin
        Telemetry t = { millis(), h, sumQ / n, sumU / n, setpoint };
        xQueueOverwrite(telemetryBox, &t);
        bool online = lastHeard && millis() - lastHeard < LINK_TIMEOUT;
        digitalWrite(PIN_ONLINE, online);
        Serial.printf("%lu,%.0f,%.0f,%.3f,%.0f,%d,%d\n", (unsigned long)t.t, h * 1000, t.q, t.u,
                      setpoint * 1000, online, digitalRead(PIN_ALARM));
        sumU = sumQ = 0; n = 0;
      }
    }
    xTaskDelayUntil(&lastWake, pdMS_TO_TICKS(100));
  }
}

// Finds "key":number in a small JSON message
bool jsonNumber(const char *msg, const char *key, float *value) {
  char pattern[16];
  snprintf(pattern, sizeof pattern, "\"%s\":", key);
  const char *p = strstr(msg, pattern);
  return p && sscanf(p + strlen(pattern), "%f", value) == 1;
}

void onWebSocket(WStype_t type, uint8_t *payload, size_t length) {
  switch (type) {
    case WStype_CONNECTED:
      Serial.printf("# connected to wss://%s:%u\n", HOST, PORT);
      lastHeard = millis();
      break;
    case WStype_DISCONNECTED:
      Serial.println("# disconnected (or connection failed), retry in 3 s");
      break;
    case WStype_ERROR:
      Serial.printf("# error: %.*s\n", (int)length, (const char *)payload);
      break;
    case WStype_TEXT: {                    // {"sp":0.45,"alarm":0,...} from the twin
      lastHeard = millis();
      Command cmd = { -1, -1 };
      float v;
      if (jsonNumber((const char *)payload, "sp", &v)) cmd.setpoint = v;
      if (jsonNumber((const char *)payload, "alarm", &v)) cmd.alarm = v != 0;
      if (cmd.setpoint >= 0 || cmd.alarm >= 0) xQueueSend(commands, &cmd, 0);
      break;
    }
    default:
      break;
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  ledcAttach(PIN_PUMP, 1000, 10);      // 1 kHz, 10 bit
  pinMode(PIN_ONLINE, OUTPUT);
  pinMode(PIN_ALARM, OUTPUT);
  commands = xQueueCreate(4, sizeof(Command));
  telemetryBox = xQueueCreate(1, sizeof(Telemetry));

  Serial.println("t_ms,h_mm,q_mls,u,sp_mm,online,alarm");
  xTaskCreate(controlTask, "control", 4096, NULL, 3, NULL);   // runs before Wi-Fi is up

  Serial.println("# wifi: connecting to Wokwi-GUEST");
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) delay(250);
  Serial.printf("# wifi: connected, IP %s\n", WiFi.localIP().toString().c_str());
  Serial.printf("# connecting to wss://%s:%u ...\n", HOST, PORT);

  char url[48], header[64];
  snprintf(url, sizeof url, "/device?id=%s", DEVICE);
  snprintf(header, sizeof header, "Authorization: Bearer %s", TOKEN);
  ws.setExtraHeaders(header);
  ws.onEvent(onWebSocket);
  ws.setReconnectInterval(3000);
  ws.beginSslWithCA(HOST, PORT, url, CA_CERT, "twin");
}

void loop() {
  ws.loop();                           // TLS, WebSocket frames, reconnect
  Telemetry t;
  if (ws.isConnected() && xQueueReceive(telemetryBox, &t, 0) == pdTRUE) {
    char msg[96];
    snprintf(msg, sizeof msg, "{\"t\":%lu,\"h\":%.3f,\"q\":%.0f,\"u\":%.3f,\"sp\":%.3f}",
             (unsigned long)t.t, t.h, t.q, t.u, t.sp);
    ws.sendTXT(msg);
  }
  delay(10);
}
