/* Register access with a struct overlay - the style of the Pico SDK and
 * of the CMSIS headers. Compile: arm-none-eabi-gcc -mcpu=cortex-m0plus
 * -mthumb -Os -c register_struct.c */
#include <stdint.h>

typedef struct {
    volatile uint32_t cpuid;          /* 0x000 */
    volatile uint32_t gpio_in;        /* 0x004 */
    volatile uint32_t gpio_hi_in;     /* 0x008 */
    uint32_t _reserved;               /* 0x00c */
    volatile uint32_t gpio_out;       /* 0x010 */
    volatile uint32_t gpio_out_set;   /* 0x014 */
    volatile uint32_t gpio_out_clr;   /* 0x018 */
    volatile uint32_t gpio_out_xor;   /* 0x01c */
    volatile uint32_t gpio_oe;        /* 0x020 */
    volatile uint32_t gpio_oe_set;    /* 0x024 */
} sio_hw_t;

#define sio_hw ((sio_hw_t *)0xd0000000u)

/* The compiler checks the offsets for us */
_Static_assert(__builtin_offsetof(sio_hw_t, gpio_out_xor) == 0x01c, "offset");
_Static_assert(__builtin_offsetof(sio_hw_t, gpio_oe_set) == 0x024, "offset");

void led_init(unsigned pin) { sio_hw->gpio_oe_set = 1u << pin; }
void led_toggle(unsigned pin) { sio_hw->gpio_out_xor = 1u << pin; }

/* Bit manipulation in a read-modify-write register */
static inline uint32_t set_field(uint32_t reg, unsigned shift, uint32_t mask, uint32_t value) {
    return (reg & ~(mask << shift)) | ((value & mask) << shift);
}

uint32_t example(uint32_t ctrl) {
    return set_field(ctrl, 4, 0x3u, 2u);   /* bits 5..4 := 2 */
}
