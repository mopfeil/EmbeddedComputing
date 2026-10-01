	.file	"sum.c"
__SP_H__ = 0x3e
__SP_L__ = 0x3d
__SREG__ = 0x3f
__tmp_reg__ = 0
__zero_reg__ = 1
	.text
.global	sum
	.type	sum, @function
sum:
/* prologue: function */
/* frame size = 0 */
/* stack size = 0 */
.L__stack_usage = 0
	movw r20,r22
	movw r30,r24
	ldi r19,0
	ldi r18,0
	ldi r22,0
	ldi r23,0
	movw r24,r22
.L2:
	cp r18,r20
	cpc r19,r21
	brlt .L3
/* epilogue start */
	ret
.L3:
	ld r26,Z+
	ld r27,Z+
	add r22,r26
	adc r23,r27
	adc r24,__zero_reg__
	adc r25,__zero_reg__
	subi r18,-1
	sbci r19,-1
	rjmp .L2
	.size	sum, .-sum
	.ident	"GCC: (GNU) 7.3.0"
