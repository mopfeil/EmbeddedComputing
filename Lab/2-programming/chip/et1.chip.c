// ET1 robot: motor driver (L298N-like H-bridge), two DC motors with wheels,
// differential drive, seen from above. The environment model for lab task 2.
//
//   ENA, IN1, IN2   left motor  (motor 1): ENA = PWM (speed), IN1/IN2 = direction
//   ENB, IN3, IN4   right motor (motor 2): ENB = PWM (speed), IN3/IN4 = direction
//
//   IN1 IN2 | motor            (IN3/IN4 the same for the right motor)
//    1   0  | forward, speed = duty cycle of ENA
//    0   1  | backward
//    0   0  | brake            1 1 also brakes
//
// Up to 12 % duty cycle a motor does not turn (friction). PWM frequency:
// 20 Hz or more. A motor needs
// about 0.15 s to reach its speed and brakes faster. Top speed 0.25 m/s,
// wheel distance 14 cm. Control "weak": the left motor is weaker by this
// many percent (real motors are never equal).
//
// The display shows a 2 m x 2 m floor (grid lines every 0.5 m), the robot
// and its track. The robot starts in the centre, facing up.
//   X, Y  position in m (start = 0, 0; Y = initial driving direction)
//   H     heading in degrees (0 = initial direction, + = turned left)
//   D     distance from the start point in m
//   L, R  speed of the left and right wheel in % of the top speed
// Each time the robot comes to a stop, the chip prints its position.

#include "wokwi-api.h"
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define STEP_NS   10000000ull     // model step 10 ms
#define DT        0.01f
#define VMAX      0.25f           // m/s at 100 % duty cycle
#define DEAD      0.12f           // duty cycle up to which the motor does not turn
#define NO_PWM_NS 50000000ull     // no EN edge for 50 ms: EN is constant
#define TAU       0.15f           // s, time constant of motor + robot
#define TAU_BRAKE 0.05f           // s, when braking
#define V_STILL   0.002f          // m/s, slower counts as standing still
#define TRACK     0.14f           // m, distance between the wheels
#define ARENA     2.0f            // m, side of the floor
#define W         128
#define TEXT_H    36
#define H         (W + TEXT_H)
#define PX_PER_M  (W / ARENA)

typedef struct {
  pin_t en, in_a, in_b;
  uint64_t last_rise, last_edge;  // times of the last EN edges
  float duty;                     // of the last complete PWM period
  bool level;
  float v;                        // wheel speed in m/s
  float gain;
} motor_t;

typedef struct {
  motor_t m[2];                   // 0 = left, 1 = right
  uint32_t weak_attr;
  float x, y, th;                 // position (m) and heading (rad, 0 = up)
  int still_steps;
  bool moved, wall_reported;
  buffer_t fb;
  uint32_t fb_w, fb_h;
  uint8_t trace[W * W];
  uint32_t pixels[W * H];
  int frame;
} chip_t;

#define RGB(r, g, b) (0xff000000u | (b) << 16 | (g) << 8 | (r))   // RGBA in memory

// --- a 3x5 pixel font, drawn twice as large ----------------------------
static const char GLYPH_CHARS[] = "0123456789+-. XYHDLR%";
static const uint8_t GLYPHS[][5] = {   // 3 bits per row, MSB = left
  {7, 5, 5, 5, 7}, {2, 6, 2, 2, 7}, {7, 1, 7, 4, 7}, {7, 1, 7, 1, 7}, {5, 5, 7, 1, 1},
  {7, 4, 7, 1, 7}, {7, 4, 7, 5, 7}, {7, 1, 1, 1, 1}, {7, 5, 7, 5, 7}, {7, 5, 7, 1, 7},
  {0, 2, 7, 2, 0}, {0, 0, 7, 0, 0}, {0, 0, 0, 0, 2}, {0, 0, 0, 0, 0}, {5, 5, 2, 5, 5},
  {5, 5, 2, 2, 2}, {5, 5, 7, 5, 5}, {6, 5, 5, 5, 6}, {4, 4, 4, 4, 7}, {6, 5, 6, 5, 5},
  {5, 1, 2, 4, 5},
};

static void put(chip_t *c, int x, int y, uint32_t color) {
  if (x >= 0 && x < W && y >= 0 && y < H) c->pixels[y * W + x] = color;
}

static void text(chip_t *c, int x, int y, const char *s, uint32_t color) {
  for (; *s; s++, x += 8) {
    const char *p = strchr(GLYPH_CHARS, *s);
    if (!p) continue;
    const uint8_t *g = GLYPHS[p - GLYPH_CHARS];
    for (int r = 0; r < 5; r++)
      for (int col = 0; col < 3; col++)
        if (g[r] & (4 >> col))
          for (int dy = 0; dy < 2; dy++)
            for (int dx = 0; dx < 2; dx++) put(c, x + 2 * col + dx, y + 2 * r + dy, color);
  }
}

// floor coordinates (m) -> pixel; the floor is below the text area
static int px(float x) { return (int)floorf(W / 2 + x * PX_PER_M); }
static int py(float y) { return (int)floorf(TEXT_H + W / 2 - y * PX_PER_M); }

static void draw(chip_t *c) {
  for (int i = 0; i < W * TEXT_H; i++) c->pixels[i] = RGB(20, 20, 28);
  for (int y = 0; y < W; y++)
    for (int x = 0; x < W; x++) {
      bool grid = (x % 32 == 0) || (y % 32 == 0);
      uint32_t col = c->trace[y * W + x] ? RGB(255, 200, 0) : grid ? RGB(70, 70, 80) : RGB(40, 40, 48);
      c->pixels[(TEXT_H + y) * W + x] = col;
    }
  // start mark
  for (int d = -2; d <= 2; d++) {
    put(c, px(0) + d, py(0), RGB(0, 200, 0));
    put(c, px(0), py(0) + d, RGB(0, 200, 0));
  }
  // robot: a disc of 8 cm radius with a line pointing forward
  int cx = px(c->x), cy = py(c->y), r = (int)(0.08f * PX_PER_M);
  for (int dy = -r; dy <= r; dy++)
    for (int dx = -r; dx <= r; dx++)
      if (dx * dx + dy * dy <= r * r) put(c, cx + dx, cy + dy, RGB(60, 140, 230));
  for (int i = 0; i <= r + 2; i++)
    put(c, cx - (int)lroundf(i * sinf(c->th)), cy - (int)lroundf(i * cosf(c->th)), RGB(255, 255, 255));

  char line[24];
  float deg = c->th * 180.0f / (float)M_PI;
  deg = fmodf(deg + 540.0f, 360.0f) - 180.0f;
  snprintf(line, sizeof line, "X%+.2f Y%+.2f", c->x, c->y);
  text(c, 2, 1, line, RGB(230, 230, 230));
  snprintf(line, sizeof line, "H%+04d D %.2f", (int)lroundf(deg), hypotf(c->x, c->y));
  text(c, 2, 13, line, RGB(230, 230, 230));
  snprintf(line, sizeof line, "L%+04d%% R%+04d%%", (int)lroundf(c->m[0].v / VMAX * 100),
           (int)lroundf(c->m[1].v / VMAX * 100));
  text(c, 2, 25, line, RGB(255, 200, 0));
  buffer_write(c->fb, 0, c->pixels, sizeof c->pixels);
}

static void on_en_change(void *user_data, pin_t pin, uint32_t value) {
  motor_t *m = user_data;
  uint64_t now = get_sim_nanos();
  if (value && m->last_rise && m->last_edge > m->last_rise)   // a full period: rise, fall, rise
    m->duty = (float)(m->last_edge - m->last_rise) / (float)(now - m->last_rise);
  if (value) m->last_rise = now;
  m->last_edge = now;
  m->level = value;
}

static float motor_step(motor_t *m, uint64_t now) {
  if (now - m->last_edge > NO_PWM_NS) m->duty = m->level;      // 0 % or 100 %
  float duty = m->duty;
  bool a = pin_read(m->in_a), b = pin_read(m->in_b);
  int dir = (a && !b) ? 1 : (!a && b) ? -1 : 0;
  float target = duty > DEAD ? dir * m->gain * VMAX * (duty - DEAD) / (1 - DEAD) : 0;
  m->v += (target - m->v) * DT / (target == 0 ? TAU_BRAKE : TAU);
  if (fabsf(m->v) < V_STILL && fabsf(target) < V_STILL) m->v = 0;
  return m->v;
}

static void on_step(void *user_data) {
  chip_t *c = user_data;
  uint64_t now = get_sim_nanos();
  c->m[0].gain = 1.0f - attr_read_float(c->weak_attr) / 100.0f;
  c->m[1].gain = 1.0f;
  float vl = motor_step(&c->m[0], now);
  float vr = motor_step(&c->m[1], now);

  float v = (vl + vr) / 2, w = (vr - vl) / TRACK;
  c->th += w * DT;
  c->x -= v * sinf(c->th) * DT;
  c->y += v * cosf(c->th) * DT;
  float lim = ARENA / 2 - 0.08f;
  bool wall = fabsf(c->x) > lim || fabsf(c->y) > lim;
  if (c->x > lim) c->x = lim;
  if (c->x < -lim) c->x = -lim;
  if (c->y > lim) c->y = lim;
  if (c->y < -lim) c->y = -lim;
  if (wall && !c->wall_reported) printf("ET1 hits the wall at X %+.2f Y %+.2f\n", c->x, c->y);
  c->wall_reported = wall;

  int tx = px(c->x), ty = py(c->y) - TEXT_H;
  if (tx >= 0 && tx < W && ty >= 0 && ty < W) c->trace[ty * W + tx] = 1;

  if (vl == 0 && vr == 0) {
    if (c->moved && ++c->still_steps == 20) {
      float deg = fmodf(c->th * 180.0f / (float)M_PI + 540.0f, 360.0f) - 180.0f;
      printf("ET1 stopped at t = %.2f s: X %+.3f m  Y %+.3f m  heading %+.1f deg  distance from start %.3f m\n",
             now / 1e9, c->x, c->y, deg, hypotf(c->x, c->y));
      c->moved = false;
    }
  } else {
    c->moved = true;
    c->still_steps = 0;
  }
  if (++c->frame % 5 == 0) draw(c);   // 20 frames per second
}

static void motor_init(chip_t *c, motor_t *m, const char *en, const char *a, const char *b) {
  m->en = pin_init(en, INPUT_PULLDOWN);
  m->in_a = pin_init(a, INPUT_PULLDOWN);
  m->in_b = pin_init(b, INPUT_PULLDOWN);
  const pin_watch_config_t watch = { .user_data = m, .edge = BOTH, .pin_change = on_en_change };
  pin_watch(m->en, &watch);
}

void chip_init(void) {
  chip_t *c = calloc(1, sizeof(chip_t));
  motor_init(c, &c->m[0], "ENA", "IN1", "IN2");
  motor_init(c, &c->m[1], "ENB", "IN3", "IN4");
  c->weak_attr = attr_init_float("weak", 0);
  c->fb = framebuffer_init(&c->fb_w, &c->fb_h);
  draw(c);
  const timer_config_t step = { .callback = on_step, .user_data = c };
  timer_start_ns(timer_init(&step), STEP_NS, true);
}
