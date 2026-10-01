// Fade the LED on GP15 with hardware PWM (slice 7, channel B).
// f_PWM = f_sys / (DIV * (TOP + 1)); with DIV = f_sys / 1 MHz -> 1 kHz
#include "hardware/clocks.h"
#include "hardware/pwm.h"

const uint LED = 15;
const uint16_t TOP = 999;
uint slice;

void setup() {
  gpio_set_function(LED, GPIO_FUNC_PWM);  // FUNCSEL = PWM
  slice = pwm_gpio_to_slice_num(LED);     // = 7
  uint32_t div = clock_get_hz(clk_sys) / 1000000;   // e.g. 125 or 200
  pwm_set_clkdiv_int_frac(slice, div, 0); // counter clock = 1 MHz
  pwm_set_wrap(slice, TOP);               // counts 0..TOP
  pwm_set_enabled(slice, true);
}

void loop() {
  for (int duty = 0; duty <= TOP; duty++) {        // fade in
    pwm_set_gpio_level(LED, duty);                  // duty = level / (TOP + 1)
    sleep_ms(1);
  }
  for (int duty = TOP; duty >= 0; duty--) {        // fade out
    pwm_set_gpio_level(LED, duty);
    sleep_ms(1);
  }
}
