// Connect to Wi-Fi and show what DHCP has configured.
#include <WiFi.h>

void setup() {
  Serial.begin(115200);
  WiFi.begin("Wokwi-GUEST", "", 6);         // open network, channel 6
  Serial.print("Connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(250);
    Serial.print(".");
  }
  Serial.println();

  // Layer 2: our MAC address. Layer 3: what the DHCP server assigned.
  Serial.printf("MAC address : %s\n", WiFi.macAddress().c_str());
  Serial.printf("IP address  : %s\n", WiFi.localIP().toString().c_str());
  Serial.printf("Subnet mask : %s\n", WiFi.subnetMask().toString().c_str());
  Serial.printf("Gateway     : %s\n", WiFi.gatewayIP().toString().c_str());
  Serial.printf("DNS server  : %s\n", WiFi.dnsIP().toString().c_str());
  Serial.printf("RSSI        : %d dBm\n", WiFi.RSSI());
}

void loop() {
  delay(10000);
}
