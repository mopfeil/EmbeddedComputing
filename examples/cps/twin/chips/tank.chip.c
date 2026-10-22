// Water tank: a pump fills it, a consumer draws water through a valve, and
// a leak can be opened. Level sensor and outlet flow meter on I2C (0x28).
//
//   PUMP  PWM input, duty cycle = pump speed (0..100 %)
//   SCL, SDA  I2C bus; register 0 = level in mm, register 1 = outlet flow
//             in mL/s, both 16 bit big-endian
//
// Controls on the chip: consumer valve (0..1) and leak (0..1). The leak
// water is not measured by any sensor -- only a model can notice it.
//
// Model (mass balance, Torricelli outflow):
//   A dh/dt = Q_PUMP * duty - valve * K_OUT * sqrt(h) - leak * K_LEAK * sqrt(h)

#include "wokwi-api.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define STEP_US   10000     // integration step 10 ms
#define AREA      0.04f     // tank cross-section in m^2
#define HEIGHT    1.0f      // tank height in m
#define Q_PUMP    2.0e-3f   // pump flow at full speed in m^3/s (2 L/s)
#define K_OUT     2.0e-3f   // valve fully open: 1.4 L/s at h = 0.5 m
#define K_LEAK    1.5e-3f   // leak fully open: 1.1 L/s at h = 0.5 m

typedef struct {
  pin_t pump;
  uint32_t valve_attr, leak_attr;
  float h;                  // the "true" water level in m
  float q_out;              // outlet flow in m^3/s (measured)
  uint64_t high_ns;         // time PUMP was high in the current step
  uint64_t last_edge_ns;
  uint8_t pointer;          // register pointer
  uint8_t byte_index;
  uint16_t latched;         // value being read
  uint32_t fb, fb_w, fb_h;  // small display on the chip
} chip_t;

static void on_pump(void *user_data, pin_t pin, uint32_t value) {
  chip_t *c = user_data;
  uint64_t now = get_sim_nanos();
  if (value == LOW) c->high_ns += now - c->last_edge_ns;   // falling edge: count the high time
  c->last_edge_ns = now;
}

static void draw(chip_t *c) {
  // the tank: water from the bottom, red frame while the leak is open
  int level = (int)(c->h / HEIGHT * c->fb_h);
  bool leak = attr_read_float(c->leak_attr) > 0;
  uint32_t water = 0xffd08020, air = 0xff303030, frame = leak ? 0xff2020ff : 0xffa0a0a0;   // ABGR
  for (uint32_t y = 0; y < c->fb_h; y++)
    for (uint32_t x = 0; x < c->fb_w; x++) {
      bool edge = x == 0 || x == c->fb_w - 1 || y == c->fb_h - 1;
      uint32_t color = edge ? frame : (c->fb_h - y <= (uint32_t)level) ? water : air;
      buffer_write(c->fb, (y * c->fb_w + x) * 4, &color, 4);
    }
}

static void on_step(void *user_data) {
  chip_t *c = user_data;
  uint64_t now = get_sim_nanos();
  if (pin_read(c->pump)) {                       // still high: count up to now
    c->high_ns += now - c->last_edge_ns;
    c->last_edge_ns = now;
  }
  float duty = c->high_ns / (STEP_US * 1000.0f);
  if (duty > 1) duty = 1;
  c->high_ns = 0;

  float root = sqrtf(c->h);
  float q_in = Q_PUMP * duty;
  c->q_out = attr_read_float(c->valve_attr) * K_OUT * root;
  float q_leak = attr_read_float(c->leak_attr) * K_LEAK * root;
  c->h += STEP_US / 1e6f * (q_in - c->q_out - q_leak) / AREA;
  if (c->h < 0) c->h = 0;
  if (c->h > HEIGHT) c->h = HEIGHT;              // overflow

  static int frame;
  if (++frame % 10 == 0) draw(c);                // refresh the display every 100 ms
  if (frame % 100 == 0)                          // ground truth for the log, every second
    printf("tank %llu ms: h=%.3f in=%.3f out=%.3f leak=%.3f L/s\n",
           (unsigned long long)(now / 1000000), c->h, q_in * 1e3f, c->q_out * 1e3f, q_leak * 1e3f);
}

// I2C: write sets the pointer register, read returns MSB, then LSB
static bool on_connect(void *user_data, uint32_t address, bool read) {
  chip_t *c = user_data;
  c->byte_index = 0;
  float noise = (rand() % 5 - 2) * 1e-3f;        // +-2 mm sensor noise
  c->latched = c->pointer == 0 ? (uint16_t)((c->h + noise < 0 ? 0 : c->h + noise) * 1000)
                               : (uint16_t)(c->q_out * 1e6f);
  return true;                                   // ACK
}

static uint8_t on_read(void *user_data) {
  chip_t *c = user_data;
  return c->byte_index++ == 0 ? c->latched >> 8 : c->latched & 0xff;
}

static bool on_write(void *user_data, uint8_t data) {
  chip_t *c = user_data;
  if (c->byte_index++ == 0) c->pointer = data & 0x01;
  return true;
}

static void on_disconnect(void *user_data) {}

void chip_init(void) {
  chip_t *c = calloc(1, sizeof(chip_t));
  c->pump = pin_init("PUMP", INPUT);
  c->valve_attr = attr_init_float("valve", 0.5f);
  c->leak_attr = attr_init_float("leak", 0.0f);
  c->h = 0.1f;

  const pin_watch_config_t watch = { .edge = BOTH, .pin_change = on_pump, .user_data = c };
  pin_watch(c->pump, &watch);

  const timer_config_t timer = { .callback = on_step, .user_data = c };
  timer_start(timer_init(&timer), STEP_US, true);

  const i2c_config_t i2c = {
    .user_data = c,
    .address = 0x28,
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
