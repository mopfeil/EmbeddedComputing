// Priority inversion: a low priority task L holds a lock that the high
// priority task H needs; a medium priority task M, which does not need
// the lock at all, delays H by running instead of L.
// Round 1 uses a binary semaphore, round 2 a mutex with priority inheritance.
SemaphoreHandle_t lock;
SemaphoreHandle_t done;

void busy(uint32_t ms) {             // use the CPU, do not block
  uint32_t start = millis();
  while (millis() - start < ms) {}
}

void lowTask(void *param) {
  xSemaphoreTake(lock, portMAX_DELAY);
  busy(300);                         // long work while holding the lock
  xSemaphoreGive(lock);
  vTaskDelete(NULL);
}

void mediumTask(void *param) {
  vTaskDelay(pdMS_TO_TICKS(100));
  busy(500);                         // CPU hog, independent of the lock
  vTaskDelete(NULL);
}

void highTask(void *param) {
  vTaskDelay(pdMS_TO_TICKS(50));
  uint32_t start = millis();
  xSemaphoreTake(lock, portMAX_DELAY);
  uint32_t waited = millis() - start;
  xSemaphoreGive(lock);
  Serial.printf("  H waited %lu ms for the lock\n", (unsigned long)waited);
  xSemaphoreGive(done);
  vTaskDelete(NULL);
}

void runRound(bool withMutex) {
  if (withMutex) {
    lock = xSemaphoreCreateMutex();          // with priority inheritance
  } else {
    lock = xSemaphoreCreateBinary();         // no inheritance
    xSemaphoreGive(lock);                    // binary semaphores start empty
  }
  Serial.println(withMutex ? "mutex:" : "binary semaphore:");
  xTaskCreate(lowTask, "L", 2048, NULL, 2, NULL);
  xTaskCreate(mediumTask, "M", 2048, NULL, 3, NULL);
  xTaskCreate(highTask, "H", 4096, NULL, 4, NULL);
  xSemaphoreTake(done, portMAX_DELAY);
  vTaskDelay(pdMS_TO_TICKS(600));            // let M finish
  vSemaphoreDelete(lock);
}

void setup() {
  Serial.begin(115200);
  done = xSemaphoreCreateBinary();
  vTaskPrioritySet(NULL, 5);   // create all tasks before any of them runs
  runRound(false);
  runRound(true);
}

void loop() {
  vTaskDelete(NULL);
}
