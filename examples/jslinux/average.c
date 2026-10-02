/* average.c - find the bug with GDB (JSLinux, Alpine x86_64)
 * gcc -g -O0 -o average average.c && ./average
 */
#include <stdio.h>
#include <stdint.h>

static const uint8_t readings[8] = {200, 210, 190, 205, 198, 202, 207, 195};

uint8_t average(const uint8_t *values, int n) {
    uint8_t sum = 0;
    for (int i = 0; i < n; i++)
        sum += values[i];
    return sum / n;
}

int main(void) {
    printf("average = %u (expected 200)\n", average(readings, 8));
    return 0;
}
