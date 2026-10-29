#include <stdint.h>

/* dot product of two Q15 vectors (fixed point, typical DSP kernel) */
int32_t dot_q15(const int16_t *a, const int16_t *b, int n) {
    int32_t s = 0;
    for (int i = 0; i < n; i++) {
        s += (int32_t)a[i] * b[i];
    }
    return s;
}

/* the same with float */
float dot_f32(const float *a, const float *b, int n) {
    float s = 0.0f;
    for (int i = 0; i < n; i++) {
        s += a[i] * b[i];
    }
    return s;
}
