// Toggle the LED (GP15) on every press of the button (GP14).
// Wokwi simulates contact bounce, so the input is debounced in software:
// a new level is accepted only after it was stable for 20 ms.
#include "hardware/gpio.h"

const uint LED = 15, BUTTON = 14;
const int STABLE_MS = 20;

bool stablePressed = false;   // debounced state
int counter = 0;              // how long the raw level differs from it

void setup() {
  gpio_init(LED);
  gpio_set_dir(LED, GPIO_OUT);
  gpio_init(BUTTON);
  gpio_set_dir(BUTTON, GPIO_IN);
  gpio_pull_up(BUTTON);       // button connects to GND: pressed = low
}

void loop() {
  bool rawPressed = !gpio_get(BUTTON);
  if (rawPressed != stablePressed) {
    if (++counter >= STABLE_MS) {
      stablePressed = rawPressed;
      counter = 0;
      if (stablePressed) {
        gpio_xor_mask(1u << LED);   // react on the press edge only
      }
    }
  } else {
    counter = 0;
  }
  sleep_ms(1);                // sample every 1 ms
}
