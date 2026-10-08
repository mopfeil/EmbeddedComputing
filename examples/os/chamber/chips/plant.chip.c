// Thermal plant: a small chamber with a heater and a TMP102-like
// temperature sensor on I2C (address 0x48).
//
//   HEAT  PWM input, duty cycle = heater power (0..100 %)
//   AIR   analog input from the fan chip, 0..3.3 V = no..full airflow
//   SCL, SDA  I2C bus; register 0 = temperature, 0.0625 degC per LSB
//
// Controls on the chip: ambient temperature, and "sensor fault" (the sensor
// no longer answers on the bus, as with a broken wire).
//
// Model (first order):  tau * dT/dt = K_HEAT * duty - (1 + K_AIR * air) * (T - T_amb)
// The ambient temperature is a control on the chip.

#include "wokwi-api.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define STEP_US   10000     // integration step 10 ms
#define TAU_S     12.0f     // thermal time constant
#define K_HEAT    60.0f     // temperature rise at full power without air flow
#define K_AIR     1.5f      // full air flow cools 2.5 times better

typedef struct {
  pin_t heat, air;
  uint32_t ambient_attr, fault_attr;
  float temp;               // the "true" temperature of the chamber
  uint64_t high_ns;         // time HEAT was high in the current step
  uint64_t last_edge_ns;
  uint8_t pointer;          // TMP102 pointer register
  uint8_t byte_index;
  uint16_t latched;         // value being read
  uint32_t fb, fb_w, fb_h;  // small display on the chip
} chip_t;

static void on_heat(void *user_data, pin_t pin, uint32_t value) {
  chip_t *c = user_data;
  uint64_t now = get_sim_nanos();
  if (value == LOW) c->high_ns += now - c->last_edge_ns;   // falling edge: count the high time
  c->last_edge_ns = now;
}

static uint16_t temp_register(chip_t *c) {
  int16_t raw = (int16_t)(c->temp / 0.0625f);    // 12 bit, left-justified as in the TMP102
  return (uint16_t)(raw << 4);
}

static void draw(chip_t *c) {
  // bar from blue (cold) to red (hot), height = temperature 0..80 degC
  int level = (int)(c->temp / 80.0f * c->fb_h);
  if (level < 0) level = 0;
  if (level > (int)c->fb_h) level = c->fb_h;
  uint8_t r = (uint8_t)(c->temp > 80 ? 255 : c->temp * 255 / 80);
  uint32_t hot = 0xff000000 | (uint32_t)(255 - r) << 16 | 40 << 8 | r;   // ABGR
  uint32_t bg = 0xff303030;
  for (uint32_t y = 0; y < c->fb_h; y++) {
    uint32_t color = (c->fb_h - y <= (uint32_t)level) ? hot : bg;
    for (uint32_t x = 0; x < c->fb_w; x++)
      buffer_write(c->fb, (y * c->fb_w + x) * 4, &color, 4);
  }
}

static void on_step(void *user_data) {
  chip_t *c = user_data;
  uint64_t now = get_sim_nanos();
  if (pin_read(c->heat)) {                       // still high: count up to now
    c->high_ns += now - c->last_edge_ns;
    c->last_edge_ns = now;
  }
  float duty = c->high_ns / (STEP_US * 1000.0f);
  if (duty > 1) duty = 1;
  c->high_ns = 0;

  float air = pin_adc_read(c->air) / 3.3f;
  float ambient = attr_read_float(c->ambient_attr);
  float dt = STEP_US / 1e6f;
  c->temp += dt / TAU_S * (K_HEAT * duty - (1 + K_AIR * air) * (c->temp - ambient));

  static int frame;
  if (++frame % 10 == 0) draw(c);                // refresh the display every 100 ms
  if (frame % 50 == 0)                           // ground truth for the log, every 500 ms
    printf("plant %llu ms: T=%.2f heat=%.2f air=%.2f\n",
           (unsigned long long)(now / 1000000), c->temp, duty, air);
}

// I2C: write sets the pointer register, read returns MSB, then LSB
static bool on_connect(void *user_data, uint32_t address, bool read) {
  chip_t *c = user_data;
  if (attr_read(c->fault_attr)) return false;    // NACK: nobody answers
  c->byte_index = 0;
  c->latched = c->pointer == 0 ? temp_register(c) : 0x60A0;   // 1 = config register (reset value)
  return true;                                   // ACK
}

static uint8_t on_read(void *user_data) {
  chip_t *c = user_data;
  return c->byte_index++ == 0 ? c->latched >> 8 : c->latched & 0xff;
}

static bool on_write(void *user_data, uint8_t data) {
  chip_t *c = user_data;
  if (c->byte_index++ == 0) c->pointer = data & 0x03;
  return true;
}

static void on_disconnect(void *user_data) {}

void chip_init(void) {
  chip_t *c = calloc(1, sizeof(chip_t));
  c->heat = pin_init("HEAT", INPUT);
  c->air = pin_init("AIR", ANALOG);
  c->ambient_attr = attr_init_float("ambient", 20.0f);
  c->fault_attr = attr_init("fault", 0);
  c->temp = attr_read_float(c->ambient_attr);

  const pin_watch_config_t watch = { .edge = BOTH, .pin_change = on_heat, .user_data = c };
  pin_watch(c->heat, &watch);

  const timer_config_t timer = { .callback = on_step, .user_data = c };
  timer_start(timer_init(&timer), STEP_US, true);

  const i2c_config_t i2c = {
    .user_data = c,
    .address = 0x48,
    .scl = pin_init("SCL", INPUT),
    .sda = pin_init("SDA", INPUT),
    .connect = on_connect,
    .read = on_read,
    .write = on_write,
    .disconnect = on_disconnect,
  };
  i2c_init(&i2c);

  c->fb = framebuffer_init(&c->fb_w, &c->fb_h);
  draw(c);
}
