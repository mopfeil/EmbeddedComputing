// Producer / consumer with a FreeRTOS queue: the producer samples the
// potentiometer (GPIO2) every 100 ms, the consumer averages 10 values.
const int POT = 2;
QueueHandle_t samples;

void producerTask(void *param) {
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    uint16_t raw = analogRead(POT);
    xQueueSend(samples, &raw, portMAX_DELAY);   // waits if the queue is full
    xTaskDelayUntil(&lastWake, pdMS_TO_TICKS(100));
  }
}

void consumerTask(void *param) {
  for (;;) {
    uint32_t sum = 0;
    for (int i = 0; i < 10; i++) {
      uint16_t value;
      xQueueReceive(samples, &value, portMAX_DELAY);   // waits for data
      sum += value;
    }
    Serial.printf("average of 10 samples: %lu\n", (unsigned long)(sum / 10));
  }
}

void setup() {
  Serial.begin(115200);
  samples = xQueueCreate(8, sizeof(uint16_t));   // 8 elements, copied by value
  xTaskCreate(producerTask, "producer", 2048, NULL, 2, NULL);
  xTaskCreate(consumerTask, "consumer", 4096, NULL, 1, NULL);
}

void loop() {
  vTaskDelete(NULL);
}
