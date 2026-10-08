// Coffee machine: a first embedded program (Arduino Uno).
// The machine itself (water boiler, heater, pump) is the custom chip
// coffee.chip.c -- the program only sees it through its pins:
//
//   sensor:    water temperature on A0, 10 mV per degC
//   actuators: heater on pin 8, pump on pin 9
//   user:      button on pin 2 to GND ("make coffee"), green LED on pin 7 = ready
//   (the red LED on pin 8 only shows when the heater is on)

const int PIN_TEMP = A0, PIN_HEATER = 8, PIN_PUMP = 9, PIN_BUTTON = 2, PIN_READY = 7;

const float T_ON = 91.0, T_OFF = 94.0;   // two-point control of the heater
const float T_READY = 90.0;              // hot enough for coffee
const unsigned long BREW_MS = 20000;     // 20 s at 2 ml/s = 40 ml

bool brewing = false;
unsigned long brewStart, lastPrint;

float readTemperature() {
  int raw = analogRead(PIN_TEMP);        // 0..1023 for 0..5 V
  float volts = raw * 5.0 / 1023;
  return volts * 100;                    // 10 mV per degC
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_HEATER, OUTPUT);
  pinMode(PIN_PUMP, OUTPUT);
  pinMode(PIN_READY, OUTPUT);
  pinMode(PIN_BUTTON, INPUT_PULLUP);
  Serial.println("coffee machine: heating up ...");
}

void loop() {
  float t = readTemperature();

  // control the water temperature: heater on below 91, off above 94 degC
  if (t < T_ON) digitalWrite(PIN_HEATER, HIGH);
  if (t > T_OFF) digitalWrite(PIN_HEATER, LOW);

  bool ready = t >= T_READY && !brewing;
  digitalWrite(PIN_READY, ready);

  // the user presses the button: make one cup of coffee
  if (digitalRead(PIN_BUTTON) == LOW && !brewing) {
    if (ready) {
      brewing = true;
      brewStart = millis();
      digitalWrite(PIN_PUMP, HIGH);
      Serial.println("making coffee ...");
    } else {
      Serial.print("please wait, water at ");
      Serial.print(t, 1);
      Serial.println(" C");
      delay(300);                        // do not repeat the message too fast
    }
  }
  if (brewing && millis() - brewStart >= BREW_MS) {
    brewing = false;
    digitalWrite(PIN_PUMP, LOW);
    Serial.println("enjoy your coffee!");
  }

  if (millis() - lastPrint >= 1000) {    // status once per second
    lastPrint = millis();
    Serial.print(t, 1);
    Serial.print(" C   heater ");
    Serial.print(digitalRead(PIN_HEATER) ? "on " : "off");
    Serial.print("   pump ");
    Serial.println(brewing ? "on" : "off");
  }
  delay(10);
}
