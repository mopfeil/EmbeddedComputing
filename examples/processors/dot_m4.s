	.cpu cortex-m4
	.arch armv7e-m
	.fpu fpv4-sp-d16
	.eabi_attribute 27, 1
	.eabi_attribute 28, 1
	.eabi_attribute 20, 1
	.eabi_attribute 21, 1
	.eabi_attribute 23, 3
	.eabi_attribute 24, 1
	.eabi_attribute 25, 1
	.eabi_attribute 26, 1
	.eabi_attribute 30, 2
	.eabi_attribute 34, 1
	.eabi_attribute 18, 4
	.file	"dot.c"
	.text
	.align	1
	.p2align 2,,3
	.global	dot_q15
	.syntax unified
	.thumb
	.thumb_func
	.type	dot_q15, %function
dot_q15:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	cmp	r2, #0
	ble	.L4
	push	{lr}
	subs	r3, r0, #2
	subs	r1, r1, #2
	add	r2, r3, r2, lsl #1
	movs	r0, #0
.L3:
	ldrh	lr, [r3, #2]!
	ldrh	ip, [r1, #2]!
	cmp	r3, r2
	smlabb	r0, lr, ip, r0
	bne	.L3
	pop	{pc}
.L4:
	movs	r0, #0
	bx	lr
	.size	dot_q15, .-dot_q15
	.align	1
	.p2align 2,,3
	.global	dot_f32
	.syntax unified
	.thumb
	.thumb_func
	.type	dot_f32, %function
dot_f32:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	@ link register save eliminated.
	cmp	r2, #0
	vldr.32	s0, .L16
	ble	.L14
	add	r2, r0, r2, lsl #2
.L13:
	vldmia.32	r0!, {s14}
	vldmia.32	r1!, {s15}
	cmp	r0, r2
	vfma.f32	s0, s14, s15
	bne	.L13
	bx	lr
.L14:
	bx	lr
.L17:
	.align	2
.L16:
	.word	0
	.size	dot_f32, .-dot_f32
	.ident	"GCC: (GNU) 16.1.0"
