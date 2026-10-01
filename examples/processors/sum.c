#include <stdint.h>

/* Sum of n 16 bit values - the same C code for three architectures */
uint32_t sum(const uint16_t *a, int n) {
    uint32_t s = 0;
    for (int i = 0; i < n; i++) {
        s += a[i];
    }
    return s;
}
