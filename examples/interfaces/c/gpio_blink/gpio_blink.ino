// Blink the LED on GP15 with the Pico SDK GPIO functions.
#include "hardware/gpio.h"

const uint LED = 15;

void setup() {
  gpio_init(LED);               // FUNCSEL = SIO, output disabled, value 0
  gpio_set_dir(LED, GPIO_OUT);  // enable the output driver
}

void loop() {
  gpio_put(LED, 1);
  sleep_ms(500);
  gpio_put(LED, 0);
  sleep_ms(500);
}
