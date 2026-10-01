// Watchdog demo: the main loop feeds the watchdog every 100 ms.
// Hold the button (GP14) longer than 1 s -> the program "hangs" and the
// watchdog resets the chip. After the reset the cause is printed.
#include "hardware/watchdog.h"

const uint LED = 15, BUTTON = 14;

void setup() {
  Serial1.begin(115200);
  gpio_init(LED);
  gpio_set_dir(LED, GPIO_OUT);
  gpio_init(BUTTON);
  gpio_pull_up(BUTTON);

  if (watchdog_caused_reboot()) {
    Serial1.println("Restarted by the WATCHDOG");
  } else {
    Serial1.println("Power-on reset");
  }
  watchdog_enable(1000, true);   // 1 s timeout, paused while debugging
}

void loop() {
  while (!gpio_get(BUTTON)) {
    // simulated "hang": the watchdog is no longer fed
  }
  watchdog_update();             // feed the watchdog
  gpio_xor_mask(1u << LED);
  sleep_ms(100);
}
