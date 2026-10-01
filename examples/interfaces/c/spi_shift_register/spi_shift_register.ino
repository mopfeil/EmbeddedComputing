// Drive a 74HC595 shift register (8 LEDs) over SPI0.
// GP18 = SCK -> SHCP, GP19 = TX (COPI) -> DS, GP17 = latch -> STCP
#include "hardware/spi.h"

const uint PIN_SCK = 18, PIN_COPI = 19, PIN_LATCH = 17;

void setup() {
  spi_init(spi0, 1000 * 1000);              // 1 MHz
  spi_set_format(spi0, 8, SPI_CPOL_0, SPI_CPHA_0, SPI_MSB_FIRST);   // mode 0
  gpio_set_function(PIN_SCK, GPIO_FUNC_SPI);
  gpio_set_function(PIN_COPI, GPIO_FUNC_SPI);
  gpio_init(PIN_LATCH);
  gpio_set_dir(PIN_LATCH, GPIO_OUT);
}

void show(uint8_t pattern) {
  spi_write_blocking(spi0, &pattern, 1);    // 8 clocks shift the byte in
  gpio_put(PIN_LATCH, 1);                       // rising edge on STCP copies the
  gpio_put(PIN_LATCH, 0);                       // shift register to the outputs
}

void loop() {
  static uint8_t pattern = 0x01;
  static bool left = true;
  show(pattern);
  pattern = left ? pattern << 1 : pattern >> 1;   // running light
  if (pattern == 0x80 || pattern == 0x01) left = !left;
  sleep_ms(100);
}
