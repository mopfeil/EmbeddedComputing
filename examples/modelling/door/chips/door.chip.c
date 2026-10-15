// Garage door with motor, end switches and light barrier: the environment
// model for the door controller (chapter Modelling).
//
//   UP, DOWN     inputs, motor command (high = run); both high = short circuit
//   TOP, BOTTOM  outputs, end switches (high = door fully open / closed)
//   BEAM         output, light barrier (high = beam interrupted)
//
// The door needs 5 s from closed to open. Controls: "obstacle" puts an object
// into the door opening, "jam" blocks the door mechanically. The display
// shows the door, the light beam and the obstacle.

#include "wokwi-api.h"
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STEP_US     10000         // model step 10 ms
#define TRAVEL_S    5.0f          // closed -> open
#define OBSTACLE_H  0.15f         // the obstacle stops the door at 15 % open

typedef struct {
  pin_t up, down, top, bottom, beam;
  uint32_t obstacle_attr, jam_attr;
  float pos;                      // 0 = closed, 1 = open
  bool short_reported, crash_reported;
  buffer_t fb;
  uint32_t w, h;
  uint32_t pixels[64 * 64];
  int drawn_rows;                 // what the display shows, to redraw only on change
  int drawn_obstacle;
} chip_t;

#define RGB(r, g, b) (0xff000000u | (b) << 16 | (g) << 8 | (r))   // RGBA in memory

static void fill(chip_t *c, int x0, int y0, int x1, int y1, uint32_t color) {
  for (int y = y0; y < y1; y++)
    for (int x = x0; x < x1; x++) c->pixels[y * c->w + x] = color;
}

static void draw(chip_t *c, int rows, bool obstacle) {
  int W = c->w, H = c->h;
  fill(c, 0, 0, W, H, RGB(40, 40, 48));                     // dark opening
  fill(c, 0, 0, 6, H, RGB(150, 150, 150));                  // frame
  fill(c, W - 6, 0, W, H, RGB(150, 150, 150));
  fill(c, 0, 0, W, 6, RGB(150, 150, 150));
  for (int y = 6; y < 6 + rows; y++)                        // door panel with grooves
    fill(c, 6, y, W - 6, y + 1, (rows + 5 - y) % 8 == 7 ? RGB(120, 70, 30) : RGB(190, 120, 60));
  if (obstacle) fill(c, 26, H - 10, 38, H, RGB(60, 120, 220));        // a box on the floor
  fill(c, 6, H - 5, W - 6, H - 4, obstacle ? RGB(255, 0, 0) : RGB(0, 200, 0));  // light beam
  buffer_write(c->fb, 0, c->pixels, W * H * 4);
  c->drawn_rows = rows;
  c->drawn_obstacle = obstacle;
}

static void on_step(void *user_data) {
  chip_t *c = user_data;
  bool up = pin_read(c->up), down = pin_read(c->down);
  bool obstacle = attr_read(c->obstacle_attr), jam = attr_read(c->jam_attr);

  if (up && down) {
    if (!c->short_reported) printf("motor UP and DOWN at the same time: short circuit!\n");
    c->short_reported = true;
  } else if (!jam) {
    c->short_reported = false;
    float v = 1.0f / TRAVEL_S * STEP_US / 1e6f;
    if (up) c->pos += v;
    if (down) c->pos -= v;
  }
  if (c->pos > 1) c->pos = 1;
  if (c->pos < 0) c->pos = 0;
  if (obstacle && c->pos < OBSTACLE_H) {                    // the door hits the object
    c->pos = OBSTACLE_H;
    if (!c->crash_reported) printf("CRASH: the door hits the obstacle!\n");
    c->crash_reported = true;
  }
  if (!obstacle) c->crash_reported = false;

  pin_write(c->top, c->pos >= 1);
  pin_write(c->bottom, c->pos <= 0);
  pin_write(c->beam, obstacle);

  int rows = (int)((1 - c->pos) * (c->h - 6) + 0.5f);
  if (rows != c->drawn_rows || obstacle != c->drawn_obstacle) draw(c, rows, obstacle);
}

void chip_init(void) {
  chip_t *c = calloc(1, sizeof(chip_t));
  c->up = pin_init("UP", INPUT_PULLDOWN);
  c->down = pin_init("DOWN", INPUT_PULLDOWN);
  c->top = pin_init("TOP", OUTPUT_LOW);
  c->bottom = pin_init("BOTTOM", OUTPUT_HIGH);              // starts closed
  c->beam = pin_init("BEAM", OUTPUT_LOW);
  c->obstacle_attr = attr_init("obstacle", 0);
  c->jam_attr = attr_init("jam", 0);
  c->fb = framebuffer_init(&c->w, &c->h);
  c->drawn_rows = -1;

  const timer_config_t step = { .callback = on_step, .user_data = c };
  timer_start(timer_init(&step), STEP_US, true);
}
