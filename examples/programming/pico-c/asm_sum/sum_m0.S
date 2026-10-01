@ uint32_t asm_sum(const uint16_t *a, int n)
@ Hand-written Thumb assembly for the Cortex-M0+ (RP2040).
@ AAPCS: a in r0, n in r1, result in r0. Only r0..r3 are used, so no
@ register has to be saved on the stack.
    .syntax unified
    .cpu cortex-m0plus
    .thumb
    .text
    .global asm_sum
    .type   asm_sum, %function
    .thumb_func
asm_sum:
    movs  r2, #0          @ s = 0
    cmp   r1, #0
    ble   2f              @ n <= 0: nothing to do
1:  ldrh  r3, [r0]        @ r3 = *a
    adds  r0, r0, #2      @ a++ (2 bytes)
    adds  r2, r2, r3      @ s += r3
    subs  r1, r1, #1      @ n--, sets the Z flag
    bne   1b              @ loop while n != 0
2:  movs  r0, r2          @ return s
    bx    lr
    .size asm_sum, .-asm_sum
