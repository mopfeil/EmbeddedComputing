	.cpu cortex-m0plus
	.arch armv6s-m
	.fpu softvfp
	.eabi_attribute 20, 1
	.eabi_attribute 21, 1
	.eabi_attribute 23, 3
	.eabi_attribute 24, 1
	.eabi_attribute 25, 1
	.eabi_attribute 26, 1
	.eabi_attribute 30, 2
	.eabi_attribute 34, 0
	.eabi_attribute 18, 4
	.file	"dot.c"
	.text
	.align	1
	.p2align 2,,3
	.global	dot_q15
	.syntax unified
	.code	16
	.thumb_func
	.type	dot_q15, %function
dot_q15:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	push	{r4, r5, r6, r7, lr}
	movs	r5, r0
	movs	r6, r1
	cmp	r2, #0
	ble	.L4
	movs	r3, #0
	movs	r0, #0
	lsls	r4, r2, #1
.L3:
	ldrsh	r1, [r5, r3]
	ldrsh	r2, [r6, r3]
	adds	r3, r3, #2
	muls	r2, r1
	adds	r0, r0, r2
	cmp	r4, r3
	bne	.L3
.L1:
	@ sp needed
	pop	{r4, r5, r6, r7, pc}
.L4:
	movs	r0, #0
	b	.L1
	.size	dot_q15, .-dot_q15
	.align	1
	.p2align 2,,3
	.global	dot_f32
	.syntax unified
	.code	16
	.thumb_func
	.type	dot_f32, %function
dot_f32:
	@ args = 0, pretend = 0, frame = 0
	@ frame_needed = 0, uses_anonymous_args = 0
	push	{r4, r5, r6, r7, lr}
	mov	lr, r8
	movs	r7, r0
	mov	r8, r1
	push	{lr}
	cmp	r2, #0
	ble	.L10
	movs	r4, #0
	movs	r5, #0
	lsls	r6, r2, #2
.L9:
	mov	r3, r8
	ldr	r0, [r7, r4]
	ldr	r1, [r3, r4]
	bl	__aeabi_fmul
	adds	r1, r0, #0
	adds	r0, r5, #0
	bl	__aeabi_fadd
	adds	r4, r4, #4
	adds	r5, r0, #0
	cmp	r6, r4
	bne	.L9
.L7:
	@ sp needed
	adds	r0, r5, #0
	pop	{r7}
	mov	r8, r7
	pop	{r4, r5, r6, r7, pc}
.L10:
	movs	r5, #0
	b	.L7
	.size	dot_f32, .-dot_f32
	.global	__aeabi_fadd
	.global	__aeabi_fmul
	.ident	"GCC: (GNU) 16.1.0"
