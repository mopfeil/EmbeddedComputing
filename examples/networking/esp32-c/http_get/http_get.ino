// HTTP by hand: open a TCP connection to port 80, send the request text
// and print the response. (Name resolution via DNS happens in connect().)
#include <WiFi.h>

const char *HOST = "example.com";

void setup() {
  Serial.begin(115200);
  WiFi.begin("Wokwi-GUEST", "", 6);
  while (WiFi.status() != WL_CONNECTED) delay(250);

  IPAddress addr;
  WiFi.hostByName(HOST, addr);                // DNS: name -> IPv4 address
  Serial.printf("%s = %s\n", HOST, addr.toString().c_str());

  WiFiClient client;                          // a TCP socket
  if (!client.connect(addr, 80)) {            // three-way handshake
    Serial.println("connect failed");
    return;
  }
  // HTTP/1.1 request: request line, header lines, empty line
  client.print("GET / HTTP/1.1\r\n"
               "Host: example.com\r\n"
               "Connection: close\r\n"
               "\r\n");

  // Read until the server closes the connection.
  while (client.connected() || client.available()) {
    if (client.available()) Serial.write(client.read());
  }
  client.stop();
  Serial.println("\n--- connection closed");
}

void loop() {
  delay(10000);
}
