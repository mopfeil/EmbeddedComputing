// Coffee machine: boiler with heater and pump, temperature sensor.
// This chip is the "physical world" for the program on the Pico.
//
//   HEAT  input:  high = heater on (1200 W)
//   PUMP  input:  high = pump on (2 ml/s cold water into the boiler, coffee into the cup)
//   TEMP  output: water temperature as a voltage, 10 mV per degC (like an LM35)
//
// Model, every 10 ms:  m c dT/dt = P_heater - k (T - T_room) - flow c (T - T_room)

#include "wokwi-api.h"
#include <stdlib.h>

#define DT        0.01f     // time step [s]
#define MASS      0.1f      // water in the boiler [kg]
#define C_WATER   4186.0f   // specific heat [J/(kg K)]
#define P_HEATER  1200.0f   // [W]
#define K_LOSS    1.0f      // heat loss to the room [W/K]
#define FLOW      0.002f    // pump: 2 g of water per second [kg/s]
#define T_ROOM    20.0f
#define CUP_ML    40.0f     // a full cup

typedef struct {
  pin_t heat, pump, temp;
  float t_water;            // water temperature [degC]
  float cup_ml;             // coffee in the cup
  uint32_t fb, w, h;        // display: the cup
} chip_t;

static void draw_cup(chip_t *c) {
  uint32_t level = (uint32_t)(c->cup_ml / CUP_ML * (c->h - 4));
  for (uint32_t y = 0; y < c->h; y++) {
    for (uint32_t x = 0; x < c->w; x++) {
      uint32_t color = 0xffffffff;                         // white background (ABGR)
      bool wall = x < 2 || x >= c->w - 2 || y >= c->h - 2;
      if (wall) color = 0xff404040;                        // the cup
      else if (y >= c->h - 2 - level) color = 0xff1a3c6f;  // coffee (brown)
      buffer_write(c->fb, (y * c->w + x) * 4, &color, 4);
    }
  }
}

static void step(void *user_data) {
  chip_t *c = user_data;
  float power = pin_read(c->heat) ? P_HEATER : 0;
  float flow = pin_read(c->pump) ? FLOW : 0;

  float loss = K_LOSS * (c->t_water - T_ROOM);
  float cold_water = flow * C_WATER * (c->t_water - T_ROOM);
  c->t_water += DT * (power - loss - cold_water) / (MASS * C_WATER);
  if (c->t_water > 100) c->t_water = 100;                 // boiling: no higher

  pin_dac_write(c->temp, c->t_water * 0.01f);              // 10 mV per degC

  static bool pumping;
  if (flow > 0 && !pumping) c->cup_ml = 0;                 // new coffee: new cup
  pumping = flow > 0;
  if (pumping && c->cup_ml < CUP_ML) c->cup_ml += flow * 1000 * DT;   // 1 g = 1 ml
  static int frame;
  if (++frame % 10 == 0) draw_cup(c);                      // 10 frames per second
}

void chip_init(void) {
  chip_t *c = calloc(1, sizeof(chip_t));
  c->heat = pin_init("HEAT", INPUT);
  c->pump = pin_init("PUMP", INPUT);
  c->temp = pin_init("TEMP", ANALOG);
  c->t_water = T_ROOM;
  c->fb = framebuffer_init(&c->w, &c->h);
  draw_cup(c);

  const timer_config_t timer = { .callback = step, .user_data = c };
  timer_start(timer_init(&timer), 10000, true);            // every 10 ms
}
