CFLAGS = -O0 -g -Wall -Wextra

dangling: dangling.c
	$(CC) $(CFLAGS) -o $@ $<

dangling_asan: dangling.c
	$(CC) $(CFLAGS) -fsanitize=address -o $@ $<

run: dangling
	./dangling

asan: dangling_asan
	./dangling_asan

clean:
	rm -f dangling dangling_asan

.PHONY: run asan clean
