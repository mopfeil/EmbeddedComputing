/*
 * One line of inline assembly makes a program much faster.
 *
 * Task: compute the CRC-32C checksum of a 1 MiB "firmware image", as a
 * bootloader does before it starts or installs an update.
 * CRC-32C (Castagnoli) is also used by iSCSI, ext4, Btrfs and SCTP.
 *
 * Three versions of the same function:
 *   1. bitwise   - 8 shift/XOR steps per byte, as found in many MCU projects
 *   2. table     - one table lookup per byte (1 KiB table in flash)
 *   3. asm       - ONE instruction per 8 bytes: x86-64 "crc32q" (SSE4.2)
 *                  or AArch64 "crc32cx" (ARMv8 CRC extension)
 *
 * Why does the compiler not use the instruction by itself? It must assume
 * the baseline instruction set (x86-64 from 2003, ARMv8.0), and neither
 * guarantees a CRC instruction. Inline assembly tells it: this CPU has it.
 * (The clean alternative are intrinsics plus a target flag, e.g.
 * _mm_crc32_u64() with -msse4.2, or __crc32cd() with -march=armv8-a+crc.)
 *
 * Build and run:  make run     (or: gcc -O2 -o crc32c crc32c.c && ./crc32c)
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define POLY 0x82F63B78u          /* CRC-32C polynomial, bit reversed */
#define IMAGE_SIZE (1u << 20)     /* 1 MiB */
#define REPEAT 20                 /* checksum the image 20 times */

/* 1. bitwise: 8 steps per byte */
static uint32_t crc32c_bitwise(const uint8_t *p, size_t n)
{
    uint32_t crc = 0xFFFFFFFFu;
    while (n--) {
        crc ^= *p++;
        for (int k = 0; k < 8; k++)
            crc = (crc >> 1) ^ (POLY & -(crc & 1u));
    }
    return ~crc;
}

/* 2. table: one lookup per byte */
static uint32_t table[256];

static void table_init(void)
{
    for (uint32_t i = 0; i < 256; i++) {
        uint32_t c = i;
        for (int k = 0; k < 8; k++)
            c = (c >> 1) ^ (POLY & -(c & 1u));
        table[i] = c;
    }
}

static uint32_t crc32c_table(const uint8_t *p, size_t n)
{
    uint32_t crc = 0xFFFFFFFFu;
    while (n--)
        crc = (crc >> 8) ^ table[(crc ^ *p++) & 0xFFu];
    return ~crc;
}

/* 3. inline assembly: one CPU instruction per 8 bytes */
static uint32_t crc32c_asm(const uint8_t *p, size_t n)
{
    uint64_t crc = 0xFFFFFFFFu;
    for (; n >= 8; p += 8, n -= 8) {
        uint64_t v;
        memcpy(&v, p, 8);                 /* unaligned load, becomes one mov */
#if defined(__x86_64__)
        __asm__("crc32q %1, %0" : "+r"(crc) : "rm"(v));          /* <-- the line */
#elif defined(__aarch64__)
        __asm__(".arch_extension crc\n\tcrc32cx %w0, %w0, %x1" : "+r"(crc) : "r"(v));   /* <-- the line */
#else
#error "no CRC instruction known for this CPU"
#endif
    }
    uint32_t c = (uint32_t)crc;           /* the last 0..7 bytes: table */
    while (n--)
        c = (c >> 8) ^ table[(c ^ *p++) & 0xFFu];
    return ~c;
}

static double now_s(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec * 1e-9;
}

typedef uint32_t (*crc_fn)(const uint8_t *, size_t);

static double measure(const char *name, crc_fn f, const uint8_t *img, double ref)
{
    volatile uint32_t sink = 0;
    double t0 = now_s();
    for (int r = 0; r < REPEAT; r++)
        sink ^= f(img, IMAGE_SIZE);
    double t = (now_s() - t0) / REPEAT;
    printf("%-8s crc = 0x%08X   %8.3f ms per MiB   %7.0f MB/s", name,
           (unsigned)f(img, IMAGE_SIZE), t * 1e3, IMAGE_SIZE / t / 1e6);
    if (ref > 0)
        printf("   %5.1fx faster", ref / t);
    printf("\n");
    (void)sink;
    return t;
}

int main(void)
{
    table_init();

    /* known answer test: CRC-32C("123456789") = 0xE3069283 */
    const uint8_t *chk = (const uint8_t *)"123456789";
    if (crc32c_bitwise(chk, 9) != 0xE3069283u || crc32c_table(chk, 9) != 0xE3069283u ||
        crc32c_asm(chk, 9) != 0xE3069283u) {
        puts("self test FAILED");
        return 1;
    }

    uint8_t *img = malloc(IMAGE_SIZE);
    uint32_t x = 12345;                       /* pseudo random "firmware" */
    for (size_t i = 0; i < IMAGE_SIZE; i++) {
        x = x * 1103515245u + 12345u;
        img[i] = (uint8_t)(x >> 16);
    }

    printf("CRC-32C of a 1 MiB image (mean of %d runs)\n", REPEAT);
    double t_bit = measure("bitwise", crc32c_bitwise, img, 0);
    measure("table", crc32c_table, img, t_bit);
    measure("asm", crc32c_asm, img, t_bit);
    free(img);
    return 0;
}
