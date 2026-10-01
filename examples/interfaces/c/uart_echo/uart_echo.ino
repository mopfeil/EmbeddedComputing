// UART echo with the Pico SDK: every received character is sent back in
// upper case. Type into the Wokwi serial monitor.
#include <ctype.h>
#include "hardware/uart.h"

void setup() {
  uart_init(uart0, 115200);                 // 8N1 is the default format
  gpio_set_function(0, GPIO_FUNC_UART);     // GP0 = TX
  gpio_set_function(1, GPIO_FUNC_UART);     // GP1 = RX
  uart_puts(uart0, "UART echo ready\r\n");
}

void loop() {
  if (uart_is_readable(uart0)) {            // RX FIFO not empty?
    char c = uart_getc(uart0);
    uart_putc_raw(uart0, toupper(c));
  }
}
