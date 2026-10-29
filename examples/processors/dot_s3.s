	.file	"dot.c"
	.text
	.align	4
	.global	dot_q15
	.type	dot_q15, @function
dot_q15:
	entry	sp, 32
	blti	a4, 1, .L4
	add.n	a4, a4, a4
	addi	a8, a4, -2
	srli	a8, a8, 1
	movi.n	a10, 0
	mov.n	a9, a2
	wsr	a10, ACCLO
	addi.n	a8, a8, 1
	loop	a8, .L3_LEND
.L3:
	l16ui	a11, a9, 0
	l16ui	a10, a3, 0
	addi.n	a9, a9, 2
	mula.aa.ll	a11, a10
	addi.n	a3, a3, 2
	.L3_LEND:
	j	.L1
.L4:
	movi.n	a8, 0
	wsr	a8, ACCLO
.L1:
	rsr	a2, ACCLO
	retw.n
	.size	dot_q15, .-dot_q15
	.align	4
	.global	dot_f32
	.type	dot_f32, @function
dot_f32:
	entry	sp, 32
	blti	a4, 1, .L11
	slli	a8, a4, 2
	addi	a8, a8, -4
	srli	a8, a8, 2
	movi.n	a9, 0
	wfr	f0, a9
	addi.n	a8, a8, 1
	loop	a8, .L10_LEND
.L10:
	lsi	f1, a2, 0
	lsi	f2, a3, 0
	addi.n	a2, a2, 4
	madd.s	f0, f1, f2
	addi.n	a3, a3, 4
	.L10_LEND:
	j	.L8
.L11:
	movi.n	a8, 0
	wfr	f0, a8
.L8:
	rfr	a2, f0
	retw.n
	.size	dot_f32, .-dot_f32
	.ident	"GCC: (crosstool-NG esp-14.2.0_20260121) 14.2.0"
