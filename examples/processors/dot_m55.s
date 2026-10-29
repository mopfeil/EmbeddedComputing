	.arch armv8.1-m.main
	.fpu fpv5-d16
	.arch_extension dsp
	.arch_extension fp
	.arch_extension fp.dp
	.arch_extension mve
	.arch_extension mve.fp
	.eabi_attribute 5, "cortex-m55"
	.eabi_attribute 28, 1
	.eabi_attribute 20, 1
	.eabi_attribute 21, 1
	.eabi_attribute 23, 3
	.eabi_attribute 24, 1
	.eabi_attribute 25, 1
	.eabi_attribute 26, 1
	.eabi_attribute 30, 2
	.eabi_attribute 34, 1
	.eabi_attribute 38, 1
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
	lsls	r2, r2, #1
	push	{lr}
	sub	lr, r2, #2
	lsr	lr, lr, #1
	add	lr, lr, #1
	subs	r3, r0, #2
	dls	lr, lr
	movs	r0, #0
	subs	r1, r1, #2
.L3:
	ldrh	ip, [r3, #2]!
	ldrh	r2, [r1, #2]!
	smlabb	r0, ip, r2, r0
	le	lr, .L3
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
	push	{r4, r5, lr}
	mov	r4, r1
	subs	r1, r2, #0
	ble	.L15
	subs	r3, r1, #1
	cmp	r3, #2
	bls	.L16
	lsrs	r2, r1, #2
	lsl	lr, r2, #4
	sub	lr, lr, #16
	lsr	lr, lr, #4
	add	lr, lr, #1
	mov	ip, r0
	mov	r3, r4
	vldr.32	s0, .L19
	dls	lr, lr
.L14:
	vldrw.32	q2, [r3], #16
	vldrw.32	q3, [ip], #16
	vmul.f32	q3, q3, q2
	vmov.32	r5, q3[1]
	vadd.f32	s0, s0, s12
	vmov	s10, r5
	vmov.32	r5, q3[2]
	vadd.f32	s0, s0, s10
	vmov	s11, r5
	vadd.f32	s0, s0, s11
	vadd.f32	s0, s0, s15
	le	lr, .L14
	cmp	r1, r2, lsl #2
	beq	.L11
	lsls	r3, r2, #2
.L13:
	add	ip, r0, r3, lsl #2
	add	r2, r4, r3, lsl #2
	vldr.32	s14, [ip]
	vldr.32	s15, [r2]
	adds	r2, r3, #1
	cmp	r1, r2
	vfma.f32	s0, s14, s15
	lsl	ip, r3, #2
	ble	.L11
	add	r2, ip, #4
	add	lr, r0, r2
	add	r2, r2, r4
	vldr.32	s14, [lr]
	vldr.32	s15, [r2]
	adds	r3, r3, #2
	cmp	r1, r3
	vfma.f32	s0, s14, s15
	ble	.L11
	add	r4, r4, ip
	add	r0, r0, ip
	vldr.32	s14, [r4, #8]
	vldr.32	s15, [r0, #8]
	vfma.f32	s0, s14, s15
.L11:
	pop	{r4, r5, pc}
.L15:
	vldr.32	s0, .L19
	pop	{r4, r5, pc}
.L16:
	movs	r3, #0
	vldr.32	s0, .L19
	b	.L13
.L20:
	.align	2
.L19:
	.word	0
	.size	dot_f32, .-dot_f32
	.ident	"GCC: (GNU) 16.1.0"
