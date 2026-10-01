	.cpu cortex-m0plus
	.arch armv6s-m
	.fpu softvfp
	.eabi_attribute 20, 1
	.eabi_attribute 21, 1
	.eabi_attribute 23, 3
	.eabi_attribute 24, 1
	.eabi_attribute 25, 1
	.eabi_attribute 26, 1
	.eabi_attribute 30, 4
	.eabi_attribute 34, 0
	.eabi_attribute 18, 4
	.file	"sum.c"
	.text
	.align	1
	.global	sum
	.syntax unified
	.code	16
	.thumb_func
	.type	sum, %function
sum:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	movs	r3, #0
	movs	r2, r3
	push	{r4, lr}
.L2:
	cmp	r3, r1
	blt	.L3
	@ sp needed
	movs	r0, r2
	pop	{r4, pc}
.L3:
	lsls	r4, r3, #1
	ldrh	r4, [r0, r4]
	adds	r3, r3, #1
	adds	r2, r2, r4
	b	.L2
	.size	sum, .-sum
	.ident	"GCC: (GNU) 16.1.0"
