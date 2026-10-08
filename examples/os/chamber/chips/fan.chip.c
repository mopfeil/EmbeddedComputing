// Fan with tachometer, like a 4-pin PC fan.
//
//   PWM   input, duty cycle = speed demand (0..100 % -> 0..3000 rpm)
//   TACH  output, 2 pulses per revolution
//   AIR   analog output to the plant, 0..3.3 V = no..full airflow
//
// The rotor follows the demand with a time constant of 0.5 s.
// The switch "stall" blocks the rotor: the fan gets power but does not turn.

#include "wokwi-api.h"
#include <stdint.h>
#include <stdlib.h>

#define STEP_US   10000     // model step 10 ms
#define MAX_RPM   3000.0f
#define TAU_S     0.5f

typedef struct {
  pin_t pwm, tach, air;
  uint32_t stall_attr;
  float rpm;
  uint64_t high_ns, last_edge_ns;
  timer_t tach_timer;
  bool tach_running;
  uint64_t next_edge_ns;
} chip_t;

static void on_pwm(void *user_data, pin_t pin, uint32_t value) {
  chip_t *c = user_data;
  uint64_t now = get_sim_nanos();
  if (value == LOW) c->high_ns += now - c->last_edge_ns;
  c->last_edge_ns = now;
}

// Toggles TACH: 2 pulses per revolution = 4 edges per revolution
static void on_tach(void *user_data) {
  chip_t *c = user_data;
  if (c->rpm < 30) {                             // standing still: no more edges
    c->tach_running = false;
    return;
  }
  pin_write(c->tach, !pin_read(c->tach));
  uint64_t half_period_ns = (uint64_t)(60e9 / (c->rpm * 4));
  c->next_edge_ns = get_sim_nanos() + half_period_ns;
  timer_start_ns(c->tach_timer, half_period_ns, false);
}

static void on_step(void *user_data) {
  chip_t *c = user_data;
  uint64_t now = get_sim_nanos();
  if (pin_read(c->pwm)) {
    c->high_ns += now - c->last_edge_ns;
    c->last_edge_ns = now;
  }
  float duty = c->high_ns / (STEP_US * 1000.0f);
  if (duty > 1) duty = 1;
  c->high_ns = 0;

  float target = attr_read(c->stall_attr) ? 0 : duty * MAX_RPM;
  c->rpm += STEP_US / 1e6f / TAU_S * (target - c->rpm);
  pin_dac_write(c->air, 3.3f * c->rpm / MAX_RPM);

  if (c->rpm >= 30 && !c->tach_running) {        // start the pulse train
    c->tach_running = true;
    on_tach(c);
  } else if (c->tach_running) {                  // speeding up: do not wait for the old edge
    uint64_t half_period_ns = (uint64_t)(60e9 / (c->rpm * 4));
    if (c->next_edge_ns > now + half_period_ns) {
      c->next_edge_ns = now + half_period_ns;
      timer_start_ns(c->tach_timer, half_period_ns, false);
    }
  }
}

void chip_init(void) {
  chip_t *c = calloc(1, sizeof(chip_t));
  c->pwm = pin_init("PWM", INPUT);
  c->tach = pin_init("TACH", OUTPUT_HIGH);       // open-collector output with pull-up on a real fan
  c->air = pin_init("AIR", ANALOG);
  c->stall_attr = attr_init("stall", 0);

  const pin_watch_config_t watch = { .edge = BOTH, .pin_change = on_pwm, .user_data = c };
  pin_watch(c->pwm, &watch);

  const timer_config_t tach = { .callback = on_tach, .user_data = c };
  c->tach_timer = timer_init(&tach);

  const timer_config_t step = { .callback = on_step, .user_data = c };
  timer_start(timer_init(&step), STEP_US, true);
}
