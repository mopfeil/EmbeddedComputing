/* Average of sensor readings - with a bug to find in the debugger.
 * Cross-compile with the Yocto SDK:   $CC -g -Og -o sensor_avg sensor_avg.c
 * Run on the PC:                       qemu-aarch64 -L $SDKTARGETSYSROOT ./sensor_avg
 * Debug:                               qemu-aarch64 -L $SDKTARGETSYSROOT -g 1234 ./sensor_avg
 *                                      $GDB ./sensor_avg  ->  target remote :1234
 */
#include <stdio.h>
#include <stdint.h>

#define N 8

/* readings of an 8 bit ADC */
static const uint8_t readings[N] = {200, 210, 190, 205, 198, 202, 207, 195};

uint8_t average(const uint8_t *values, int n) {
    uint8_t sum = 0;                 /* BUG: too small for the sum of 8 values */
    for (int i = 0; i < n; i++) {
        sum += values[i];
    }
    return sum / n;
}

int main(void) {
    printf("average = %u (expected 200)\n", average(readings, N));
    return 0;
}
