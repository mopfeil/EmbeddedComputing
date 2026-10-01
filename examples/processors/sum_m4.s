	.cpu cortex-m4
	.arch armv7e-m
	.fpu softvfp
	.eabi_attribute 20, 1
	.eabi_attribute 21, 1
	.eabi_attribute 23, 3
	.eabi_attribute 24, 1
	.eabi_attribute 25, 1
	.eabi_attribute 26, 1
	.eabi_attribute 30, 4
	.eabi_attribute 34, 1
	.eabi_attribute 18, 4
	.file	"sum.c"
	.text
	.align	1
	.global	sum
	.syntax unified
	.thumb
	.thumb_func
	.type	sum, %function
sum:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	push	{r4, lr}
	movs	r3, #0
	mov	r2, r3
.L2:
	cmp	r3, r1
	blt	.L3
	mov	r0, r2
	pop	{r4, pc}
.L3:
	ldrh	r4, [r0, r3, lsl #1]
	adds	r3, r3, #1
	add	r2, r2, r4
	b	.L2
	.size	sum, .-sum
	.ident	"GCC: (GNU) 16.1.0"
