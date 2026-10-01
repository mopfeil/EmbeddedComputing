// Two FreeRTOS tasks with different periods: a blinking LED (GPIO4)
// and a heartbeat message on the serial monitor.
const int LED = 4;

void blinkTask(void *param) {
  pinMode(LED, OUTPUT);
  for (;;) {
    digitalWrite(LED, !digitalRead(LED));
    vTaskDelay(pdMS_TO_TICKS(500));          // blocked for 500 ms
  }
}

void heartbeatTask(void *param) {
  TickType_t lastWake = xTaskGetTickCount();
  for (uint32_t n = 0;; n++) {
    Serial.printf("heartbeat %lu at %lu ms\n", (unsigned long)n, (unsigned long)millis());
    xTaskDelayUntil(&lastWake, pdMS_TO_TICKS(1000));   // fixed period, no drift
  }
}

void setup() {
  Serial.begin(115200);
  // function, name, stack size (ESP-IDF: in BYTES), parameter, priority, handle
  xTaskCreate(blinkTask, "blink", 2048, NULL, 2, NULL);
  xTaskCreate(heartbeatTask, "heartbeat", 4096, NULL, 1, NULL);
}

void loop() {
  vTaskDelete(NULL);   // the Arduino loop task is not needed any more
}
