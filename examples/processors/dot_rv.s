	.file	"dot.c"
	.option nopic
	.attribute arch, "rv32i2p1_m2p0_c2p0"
	.attribute unaligned_access, 0
	.attribute stack_align, 16
	.text
	.align	1
	.globl	dot_q15
	.type	dot_q15, @function
dot_q15:
	ble	a2,zero,.L4
	slli	a2,a2,1
	mv	a5,a0
	add	a2,a0,a2
	li	a0,0
.L3:
	lh	a4,0(a5)
	lh	a3,0(a1)
	addi	a5,a5,2
	addi	a1,a1,2
	mul	a4,a4,a3
	add	a0,a0,a4
	bne	a2,a5,.L3
	ret
.L4:
	li	a0,0
	ret
	.size	dot_q15, .-dot_q15
	.align	1
	.globl	dot_f32
	.type	dot_f32, @function
dot_f32:
	addi	sp,sp,-32
	sw	ra,28(sp)
	sw	s1,20(sp)
	ble	a2,zero,.L10
	slli	a2,a2,2
	sw	s0,24(sp)
	sw	s2,16(sp)
	sw	s3,12(sp)
	mv	s0,a0
	add	s3,a0,a2
	mv	s2,a1
	mv	s1,zero
.L9:
	lw	a1,0(s2)
	lw	a0,0(s0)
	addi	s0,s0,4
	addi	s2,s2,4
	call	__mulsf3
	mv	a1,a0
	mv	a0,s1
	call	__addsf3
	mv	s1,a0
	bne	s0,s3,.L9
	lw	s0,24(sp)
	lw	ra,28(sp)
	lw	s2,16(sp)
	lw	s3,12(sp)
	mv	a0,s1
	lw	s1,20(sp)
	addi	sp,sp,32
	jr	ra
.L10:
	lw	ra,28(sp)
	mv	s1,zero
	mv	a0,s1
	lw	s1,20(sp)
	addi	sp,sp,32
	jr	ra
	.size	dot_f32, .-dot_f32
	.globl	__addsf3
	.globl	__mulsf3
	.ident	"GCC: (crosstool-NG esp-14.2.0_20260121) 14.2.0"
	.section	.note.GNU-stack,"",@progbits
