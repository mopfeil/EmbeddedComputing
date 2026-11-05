# Example 1: one line of inline assembly
CC     ?= gcc
CFLAGS ?= -O2 -g -Wall -Wextra

crc32c: crc32c.c
	$(CC) $(CFLAGS) -o $@ $<

run: crc32c
	./crc32c

# show the machine code of the inner loops
asm: crc32c
	objdump -d --no-show-raw-insn crc32c | awk '/<crc32c_(table|asm)>:/,/ret/'

clean:
	rm -f crc32c

.PHONY: run asm clean
