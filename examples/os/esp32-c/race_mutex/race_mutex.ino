// Race condition: two tasks increment a shared counter 1000 times each.
// The read-modify-write is interrupted by a task switch (taskYIELD), so
// updates get lost. Round 2 protects the sequence with a mutex.
volatile uint32_t counter;
SemaphoreHandle_t lock;
SemaphoreHandle_t done;              // counting semaphore: "task finished"
bool useMutex;

void workerTask(void *param) {
  for (int i = 0; i < 1000; i++) {
    if (useMutex) xSemaphoreTake(lock, portMAX_DELAY);
    uint32_t value = counter;        // read
    taskYIELD();                     // provoke a task switch right here
    counter = value + 1;             // modify-write
    if (useMutex) xSemaphoreGive(lock);
  }
  xSemaphoreGive(done);
  vTaskDelete(NULL);
}

void runRound(bool withMutex) {
  counter = 0;
  useMutex = withMutex;
  xTaskCreate(workerTask, "w1", 2048, NULL, 2, NULL);   // same priority:
  xTaskCreate(workerTask, "w2", 2048, NULL, 2, NULL);   // taskYIELD alternates
  xSemaphoreTake(done, portMAX_DELAY);
  xSemaphoreTake(done, portMAX_DELAY);
  Serial.printf("%s mutex: counter = %lu (expected 2000)\n",
                withMutex ? "with   " : "without", (unsigned long)counter);
}

void setup() {
  Serial.begin(115200);
  lock = xSemaphoreCreateMutex();
  done = xSemaphoreCreateCounting(2, 0);
  vTaskPrioritySet(NULL, 5);   // create all tasks before any of them runs
  runRound(false);
  runRound(true);
}

void loop() {
  vTaskDelete(NULL);
}
