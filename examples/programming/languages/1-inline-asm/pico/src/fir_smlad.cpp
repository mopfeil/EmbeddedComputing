/*
 * One line of inline assembly on the Raspberry Pi Pico 2 (RP2350, Cortex-M33).
 *
 * Task: an FIR low-pass filter for audio samples (16 bit), the core of
 * every digital filter, equaliser or sensor smoothing. Its inner loop is a
 * dot product: sum of x[i] * h[i].
 *
 * The Cortex-M33 has DSP instructions. SMLAD multiplies TWO pairs of 16 bit
 * values and adds both products to an accumulator - in one instruction:
 *     acc = acc + x[0]*h[0] + x[1]*h[1]
 * The compiler does not generate it from a normal C loop, so we write
 * this one instruction as inline assembly. (CMSIS offers the same as the
 * intrinsic __SMLAD(); CMSIS-DSP's arm_fir_q15() uses it internally.)
 *
 * Board: Raspberry Pi Pico 2 (arduino-pico core via PlatformIO), simulated in Wokwi.
 * Output on Serial1 (GP0/GP1, 115200 baud).
 */
#include <Arduino.h>
#include <string.h>

#define N    1024                 // samples per block
#define TAPS 32                   // filter length
#define REPEAT 20

static int16_t x[N + TAPS];       // input with history
static int16_t h[TAPS];           // filter coefficients (Q15)
static int32_t y_c[N], y_asm[N];  // results of both versions

// 1. plain C: one multiply-accumulate per step
static int32_t dot_c(const int16_t *a, const int16_t *b, int n)
{
    int32_t s = 0;
    for (int i = 0; i < n; i++)
        s += a[i] * b[i];
    return s;
}

// 2. inline assembly: two multiply-accumulates per instruction
static int32_t dot_asm(const int16_t *a, const int16_t *b, int n)
{
    int32_t s = 0;
    for (int i = 0; i < n; i += 2) {
        uint32_t va, vb;
        memcpy(&va, a + i, 4);    // two samples in one 32 bit register
        memcpy(&vb, b + i, 4);    // two coefficients
        __asm__("smlad %0, %1, %2, %0" : "+r"(s) : "r"(va), "r"(vb));   // <-- the line
    }
    return s;
}

static uint32_t filter_block(int32_t (*dot)(const int16_t *, const int16_t *, int), int32_t *y)
{
    uint32_t t0 = micros();
    for (int r = 0; r < REPEAT; r++)
        for (int k = 0; k < N; k++)
            y[k] = dot(&x[k], h, TAPS);
    return (micros() - t0) / REPEAT;
}

void setup()
{
    Serial1.begin(115200);

    // test signal: 500 Hz tone + noise at 48 kHz; moving average as filter
    uint32_t r = 1;
    for (int i = 0; i < N + TAPS; i++) {
        r = r * 1103515245u + 12345u;
        float tone = 8000.0f * sinf(2.0f * 3.14159265f * 500.0f * i / 48000.0f);
        x[i] = (int16_t)(tone + (int16_t)(r >> 16) / 8);
    }
    for (int i = 0; i < TAPS; i++)
        h[i] = 32767 / TAPS;

    uint32_t t_c = filter_block(dot_c, y_c);
    uint32_t t_asm = filter_block(dot_asm, y_asm);

    Serial1.printf("FIR filter, %d taps, %d samples, %lu MHz\n", TAPS, N,
                   (unsigned long)(rp2040.f_cpu() / 1000000));
    Serial1.printf("C      %6lu us per block\n", (unsigned long)t_c);
    unsigned long f10 = (20ul * t_c / t_asm + 1) / 2;   // speed-up in tenths, rounded (no float printf)
    Serial1.printf("smlad  %6lu us per block   %lu.%lux faster\n",
                   (unsigned long)t_asm, f10 / 10, f10 % 10);
    Serial1.printf("results %s\n", memcmp(y_c, y_asm, sizeof y_c) == 0 ? "identical" : "DIFFERENT");
}

void loop() {}
