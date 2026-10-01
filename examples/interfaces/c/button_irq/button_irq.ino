// Toggle the LED (GP15) from an interrupt on the falling edge of GP14.
// Run it with button bouncing enabled: one press may toggle several times!
const int LED = 15, BUTTON = 14;

volatile uint32_t irqCount = 0;   // shared with the ISR -> volatile

void onButton() {                 // interrupt service routine: keep it short
  digitalWrite(LED, !digitalRead(LED));
  irqCount++;
}

void setup() {
  Serial1.begin(115200);
  pinMode(LED, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON), onButton, FALLING);
}

void loop() {
  static uint32_t last = 0;
  uint32_t now = irqCount;        // 32 bit read is atomic on the Cortex-M0+
  if (now != last) {
    Serial1.printf("interrupts so far: %lu\n", (unsigned long)now);
    last = now;
  }
}
