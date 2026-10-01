// MQTT: publish the potentiometer value (GPIO2, ADC) every 2 s and switch
// the LED (GPIO4) with messages "on" / "off" on the topic .../led.
// Change DEVICE to a unique name - the public broker is shared with everybody!
// Wokwi: add the library "PubSubClient" (Library Manager / libraries.txt).
#include <WiFi.h>
#include <PubSubClient.h>

const char *BROKER = "test.mosquitto.org";
const char *DEVICE = "rwu-ec-demo";          // <- change me
const char *TOPIC_POT = "rwu-ec/rwu-ec-demo/pot";
const char *TOPIC_LED = "rwu-ec/rwu-ec-demo/led";
const int LED = 4, POT = 2;

WiFiClient tcp;
PubSubClient mqtt(tcp);

// Called by mqtt.loop() for every received PUBLISH packet.
void onMessage(char *topic, byte *payload, unsigned int len) {
  String msg((const char *)payload, len);
  Serial.printf("received %s: %s\n", topic, msg.c_str());
  if (msg == "on") digitalWrite(LED, HIGH);
  if (msg == "off") digitalWrite(LED, LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) delay(250);

  mqtt.setServer(BROKER, 1883);              // MQTT without TLS
  mqtt.setCallback(onMessage);
}

void loop() {
  if (!mqtt.connected()) {                   // (re)connect: CONNECT + SUBSCRIBE
    if (mqtt.connect(DEVICE)) {
      mqtt.subscribe(TOPIC_LED);
      Serial.printf("connected to %s, subscribed to %s\n", BROKER, TOPIC_LED);
    } else {
      delay(2000);
      return;
    }
  }
  mqtt.loop();                               // receive packets, keep-alive

  static uint32_t last = 0;
  if (millis() - last >= 2000) {
    last = millis();
    char text[8];
    snprintf(text, sizeof text, "%d", analogRead(POT));   // 12 bit: 0..4095
    mqtt.publish(TOPIC_POT, text);
    Serial.printf("published %s = %s\n", TOPIC_POT, text);
  }
}
