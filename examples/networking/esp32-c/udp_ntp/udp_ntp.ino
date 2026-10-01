// UDP: ask a time server (NTP, port 123) for the current time.
// One request datagram, one answer datagram - no connection.
#include <WiFi.h>
#include <WiFiUdp.h>

const char *NTP_SERVER = "pool.ntp.org";
const uint32_t NTP_TO_UNIX = 2208988800UL;  // seconds 1900-01-01 .. 1970-01-01
WiFiUDP udp;

void setup() {
  Serial.begin(115200);
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) delay(250);
  udp.begin(12345);                          // local port
}

void loop() {
  uint8_t packet[48] = {0};
  packet[0] = 0b00100011;                    // LI 0, version 4, mode 3 (client)
  udp.beginPacket(NTP_SERVER, 123);
  udp.write(packet, sizeof packet);
  udp.endPacket();

  // UDP gives no guarantee: the answer may never arrive -> timeout
  uint32_t start = millis();
  while (udp.parsePacket() < 48) {
    if (millis() - start > 3000) {
      Serial.println("no answer within 3 s (UDP datagram lost?)");
      delay(10000);
      return;
    }
    delay(10);
  }
  udp.read(packet, sizeof packet);
  // Transmit timestamp: seconds since 1900 in bytes 40..43 (big endian)
  uint32_t secs = (uint32_t)packet[40] << 24 | (uint32_t)packet[41] << 16 |
                  (uint32_t)packet[42] << 8 | packet[43];
  uint32_t unixTime = secs - NTP_TO_UNIX;
  Serial.printf("%s: unix time %lu, UTC %02lu:%02lu:%02lu\n",
                udp.remoteIP().toString().c_str(), (unsigned long)unixTime,
                (unsigned long)(unixTime / 3600 % 24), (unsigned long)(unixTime / 60 % 60),
                (unsigned long)(unixTime % 60));
  delay(10000);
}
