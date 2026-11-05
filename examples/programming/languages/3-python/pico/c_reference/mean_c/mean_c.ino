/*
 * C reference for the speed test in ../main.py: the mean of 10000 ADC
 * values (12 bit) on the Raspberry Pi Pico. Output on Serial1 (GP0/GP1).
 * Build for 125 MHz like MicroPython: -b rp2040:rp2040:rpipico:freq=125
 */
#include <Arduino.h>

static uint16_t adc[10000];

static uint32_t __attribute__((noinline)) mean_c(const uint16_t *d, int n)
{
    uint32_t s = 0;
    for (int i = 0; i < n; i++)
        s += d[i];
    return s / n;
}

void setup()
{
    Serial1.begin(115200);
    for (int i = 0; i < 10000; i++)
        adc[i] = (i * 37) & 0xFFF;
    uint32_t t0 = micros();
    uint32_t m = mean_c(adc, 10000);
    uint32_t dt = micros() - t0;
    Serial1.printf("CPU clock %lu MHz\n", (unsigned long)(rp2040.f_cpu() / 1000000));
    Serial1.printf("  C (-Os)      %7lu us   mean = %lu\n", (unsigned long)dt, (unsigned long)m);
}

void loop() {}
