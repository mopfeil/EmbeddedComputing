// Interrupt -> task with a binary semaphore: the ISR only "gives" the
// semaphore, the task does the work (deferred interrupt handling).
const int LED = 4, BUTTON = 5;
SemaphoreHandle_t buttonSem;

void IRAM_ATTR onButton() {          // ISR: as short as possible
  BaseType_t woken = pdFALSE;
  xSemaphoreGiveFromISR(buttonSem, &woken);   // never the normal API in an ISR
  portYIELD_FROM_ISR(woken);         // switch at once if a higher task woke up
}

void buttonTask(void *param) {
  int presses = 0;
  for (;;) {
    xSemaphoreTake(buttonSem, portMAX_DELAY);   // sleep until the ISR gives
    presses++;
    digitalWrite(LED, !digitalRead(LED));
    Serial.printf("button pressed (%d)\n", presses);

    vTaskDelay(pdMS_TO_TICKS(50));               // debounce: ignore bouncing
    while (digitalRead(BUTTON) == LOW) vTaskDelay(pdMS_TO_TICKS(10));   // released?
    vTaskDelay(pdMS_TO_TICKS(50));
    xSemaphoreTake(buttonSem, 0);                // drop gives from the bouncing
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(LED, OUTPUT);
  pinMode(BUTTON, INPUT_PULLUP);
  buttonSem = xSemaphoreCreateBinary();
  xTaskCreate(buttonTask, "button", 4096, NULL, 3, NULL);
  attachInterrupt(digitalPinToInterrupt(BUTTON), onButton, FALLING);
}

void loop() {
  vTaskDelete(NULL);
}
