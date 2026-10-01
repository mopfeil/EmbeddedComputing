// Blink the LED on GP15 by writing the RP2040 registers directly.
// (The Arduino core has already released IO_BANK0/PADS_BANK0 from reset.)
#include <stdint.h>

#define IO_BANK0_ADDR   0x40014000u
#define SIO_ADDR        0xd0000000u

// GPIOn_CTRL: function select of pin n (8 bytes per pin, CTRL at offset 4)
#define GPIO_CTRL(n)    (*(volatile uint32_t *)(IO_BANK0_ADDR + 0x04u + 8u * (n)))
#define SIO_GPIO_OE_SET (*(volatile uint32_t *)(SIO_ADDR + 0x024u))
#define SIO_GPIO_OUT_XOR (*(volatile uint32_t *)(SIO_ADDR + 0x01cu))

#define FUNCSEL_SIO     5u
#define LED             15u

void setup() {
  GPIO_CTRL(LED)  = FUNCSEL_SIO;   // pin is controlled by software (SIO)
  SIO_GPIO_OE_SET = 1u << LED;     // enable output driver (atomic set)
}

void loop() {
  SIO_GPIO_OUT_XOR = 1u << LED;    // toggle - no read-modify-write needed
  delay(500);
}
