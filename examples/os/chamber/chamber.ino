// Climate chamber: the ESP32-C3 holds the temperature of a chamber at 40 degC.
// The chamber and the fan are not part of this program -- they are custom
// chips in the simulator (chips/plant.chip.c, chips/fan.chip.c) that play the
// physical environment. The program only sees them through its interfaces:
//
//   I2C  (SDA 8, SCL 9, 100 kHz)  TMP102-like temperature sensor 0x48, LCD 0x27
//   PWM  GPIO6 heater, GPIO7 fan
//   GPIO5 fan tachometer, 2 pulses per revolution (interrupt)
//   GPIO10 alarm LED
//
// FreeRTOS tasks (higher number = more important):
//   control (4)  PI controller, safe state on faults     <- queue from sensor
//   sensor  (3)  reads the temperature every 100 ms      -> queue to control
//   fan     (2)  rpm from the tachometer, stall detection -> event group
//   display (1)  LCD and serial log every 500 ms          <- mailbox from control
// The sensor and the display share the I2C bus, protected by a mutex.

#include <Wire.h>
#include <LiquidCrystal_I2C.h>

const int PIN_SDA = 8, PIN_SCL = 9;
const int PIN_HEAT = 6, PIN_FAN = 7, PIN_TACH = 5, PIN_ALARM = 10;
const uint8_t TMP102 = 0x48;
const float SETPOINT = 40.0;        // degC
const float KP = 0.1, KI = 0.02;    // PI controller, output 0..1

struct Measurement { float temp; };
struct Status { float temp, heat, fan; uint32_t rpm; EventBits_t faults; };

QueueHandle_t measurements;         // sensor -> control
QueueHandle_t statusBox;            // control -> display, length 1 (mailbox)
SemaphoreHandle_t i2cMutex;         // one bus, two users
EventGroupHandle_t faults;
const EventBits_t FAN_STALL = 1 << 0, SENSOR_LOST = 1 << 1;

LiquidCrystal_I2C lcd(0x27, 16, 2);
volatile uint32_t tachPulses;       // written by the ISR
volatile uint32_t fanRpm;           // written by the fan task
volatile float fanDemand;           // written by the control task

void IRAM_ATTR onTach() {
  tachPulses = tachPulses + 1;      // single writer, read with interrupts off
}

// Reads the temperature register of the TMP102: pointer 0, then two bytes
bool readTemperature(float *temp) {
  xSemaphoreTake(i2cMutex, portMAX_DELAY);
  Wire.beginTransmission(TMP102);
  Wire.write(0x00);
  bool ok = Wire.endTransmission(false) == 0 && Wire.requestFrom(TMP102, (uint8_t)2) == 2;
  int16_t raw = ok ? (int16_t)(Wire.read() << 8 | Wire.read()) : 0;
  xSemaphoreGive(i2cMutex);
  *temp = (raw >> 4) * 0.0625f;     // 12 bit, 0.0625 degC per LSB
  return ok;
}

void sensorTask(void *param) {
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    Measurement m;
    if (readTemperature(&m.temp))
      xQueueSend(measurements, &m, 0);
    xTaskDelayUntil(&lastWake, pdMS_TO_TICKS(100));
  }
}

void controlTask(void *param) {
  float integral = 0, temp = 0;
  for (;;) {
    Measurement m;
    if (xQueueReceive(measurements, &m, pdMS_TO_TICKS(500)) == pdTRUE) {
      temp = m.temp;
      xEventGroupClearBits(faults, SENSOR_LOST);
    } else {
      xEventGroupSetBits(faults, SENSOR_LOST);   // no value for 500 ms
    }
    EventBits_t f = xEventGroupGetBits(faults);

    float heat, fan;
    if (f) {                                     // safe state: heater off, full air
      heat = 0;
      fan = 1.0;
      integral = 0;
    } else {
      float error = SETPOINT - temp;
      heat = KP * error + KI * integral;
      if ((heat > 0 && heat < 1) || (heat >= 1 && error < 0) || (heat <= 0 && error > 0))
        integral += error * 0.1f;                // anti-windup: integrate only when useful
      heat = constrain(heat, 0.0f, 1.0f);
      fan = temp > SETPOINT + 3 ? 1.0 : 0.4;
    }
    ledcWrite(PIN_HEAT, heat * 1023);
    ledcWrite(PIN_FAN, fan * 1023);
    fanDemand = fan;
    digitalWrite(PIN_ALARM, f ? HIGH : LOW);

    Status s = { temp, heat, fan, fanRpm, f };
    xQueueOverwrite(statusBox, &s);              // the display always gets the latest
  }
}

void fanTask(void *param) {
  TickType_t lastWake = xTaskGetTickCount();
  int slow = 0;
  for (;;) {
    xTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
    noInterrupts();
    uint32_t pulses = tachPulses;
    tachPulses = 0;
    interrupts();
    fanRpm = pulses * 60;                        // pulses / 2 per rev / 0.5 s * 60 s
    // stalled: the fan is driven, but turns too slowly for 1 s
    slow = (fanDemand > 0.2 && fanRpm < 300) ? slow + 1 : 0;
    if (slow >= 2)
      xEventGroupSetBits(faults, FAN_STALL);
    else if (fanRpm >= 300)
      xEventGroupClearBits(faults, FAN_STALL);
  }
}

void displayTask(void *param) {
  TickType_t lastWake = xTaskGetTickCount();
  for (;;) {
    Status s;
    if (xQueuePeek(statusBox, &s, portMAX_DELAY) == pdTRUE) {
      Serial.printf("%lu,%.2f,%.2f,%.2f,%lu,%lu\n", (unsigned long)millis(),
                    s.temp, s.heat, s.fan, (unsigned long)s.rpm, (unsigned long)s.faults);
      char line1[17], line2[17];
      snprintf(line1, sizeof line1, "T %5.1fC set %2.0f", s.temp, SETPOINT);
      if (s.faults & FAN_STALL)        snprintf(line2, sizeof line2, "FAN STALLED!    ");
      else if (s.faults & SENSOR_LOST) snprintf(line2, sizeof line2, "SENSOR LOST!    ");
      else snprintf(line2, sizeof line2, "H%3d%% F%4lurpm ", (int)(s.heat * 100), (unsigned long)s.rpm);
      xSemaphoreTake(i2cMutex, portMAX_DELAY);
      lcd.setCursor(0, 0);
      lcd.print(line1);
      lcd.setCursor(0, 1);
      lcd.print(line2);
      xSemaphoreGive(i2cMutex);
    }
    xTaskDelayUntil(&lastWake, pdMS_TO_TICKS(500));
  }
}

void setup() {
  Serial.begin(115200);
  Wire.begin(PIN_SDA, PIN_SCL);
  lcd.init();
  lcd.backlight();
  ledcAttach(PIN_HEAT, 1000, 10);   // 1 kHz, 10 bit
  ledcAttach(PIN_FAN, 1000, 10);
  pinMode(PIN_ALARM, OUTPUT);
  pinMode(PIN_TACH, INPUT_PULLUP);
  attachInterrupt(PIN_TACH, onTach, RISING);

  measurements = xQueueCreate(4, sizeof(Measurement));
  statusBox = xQueueCreate(1, sizeof(Status));
  i2cMutex = xSemaphoreCreateMutex();
  faults = xEventGroupCreate();
  Serial.println("t_ms,temp,heat,fan,rpm,faults");

  xTaskCreate(controlTask, "control", 4096, NULL, 4, NULL);
  xTaskCreate(sensorTask, "sensor", 4096, NULL, 3, NULL);
  xTaskCreate(fanTask, "fan", 2048, NULL, 2, NULL);
  xTaskCreate(displayTask, "display", 4096, NULL, 1, NULL);
}

void loop() {
  vTaskDelete(NULL);
}
