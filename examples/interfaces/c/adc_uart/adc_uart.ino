// Read the potentiometer (GP26 = ADC0) and the internal temperature sensor
// (ADC4) and print the values on UART0 (GP0 = TX, GP1 = RX).
#include "hardware/adc.h"

void setup() {
  Serial1.begin(115200);           // UART0, 8N1
  adc_init();
  adc_gpio_init(26);               // disable digital input buffer on GP26
  adc_set_temp_sensor_enabled(true);
}

void loop() {
  adc_select_input(0);             // multiplexer -> channel 0 (GP26)
  uint16_t raw = adc_read();       // 12 bit: 0 .. 4095
  uint32_t millivolt = raw * 3300u / 4095u;

  adc_select_input(4);             // channel 4 = temperature sensor
  float vSense = adc_read() * 3.3f / 4095.0f;
  float celsius = 27.0f - (vSense - 0.706f) / 0.001721f;   // datasheet formula

  Serial1.printf("ADC0 = %4u (%4lu mV)   chip temperature = %.1f C\n",
                 raw, (unsigned long)millivolt, celsius);
  sleep_ms(500);
}
