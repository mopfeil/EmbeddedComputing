	.file	"sum.c"
	.option nopic
	.attribute arch, "rv32i2p1_m2p0_c2p0"
	.attribute unaligned_access, 0
	.attribute stack_align, 16
	.text
	.align	1
	.globl	sum
	.type	sum, @function
sum:
	mv	a4,a0
	li	a5,0
	li	a0,0
.L2:
	blt	a5,a1,.L3
	ret
.L3:
	slli	a3,a5,1
	add	a3,a4,a3
	lhu	a3,0(a3)
	addi	a5,a5,1
	add	a0,a0,a3
	j	.L2
	.size	sum, .-sum
	.ident	"GCC: (crosstool-NG esp-14.2.0_20260121) 14.2.0"
	.section	.note.GNU-stack,"",@progbits
