/*
 * A memory error that C accepts without complaint: a dangling pointer.
 *
 * A data logger stores sensor readings in a buffer that grows when it is
 * full (like std::vector in C++ or Vec in Rust). The program keeps a pointer
 * to the first reading. When the buffer grows, realloc() moves it to a new
 * address and frees the old one - the pointer now points to freed memory.
 *
 *   make run    normal build: prints a wrong value (or crashes), no warning
 *   make asan   with AddressSanitizer: "heap-use-after-free" at run time
 *
 * Compare with ../examples/dangling.rs: Rust rejects the same program when
 * it is compiled.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

typedef struct {
    int16_t *data;
    size_t len, cap;
} Log;

static void log_push(Log *log, int16_t value)
{
    if (log->len == log->cap) {                   /* full: grow the buffer */
        log->cap = log->cap ? 2 * log->cap : 4;
        log->data = realloc(log->data, log->cap * sizeof *log->data);
        if (!log->data)
            exit(1);
    }
    log->data[log->len++] = value;
}

int main(void)
{
    Log log = {0};
    log_push(&log, 215);                          /* 21.5 degC, in 0.1 degC */

    int16_t *first = &log.data[0];                /* remember the first reading */
    printf("first reading: %d (address %p)\n", *first, (void *)first);

    for (int i = 0; i < 100; i++)                 /* more readings: buffer grows */
        log_push(&log, (int16_t)(220 + i));

    printf("buffer is now at        %p\n", (void *)log.data);
    printf("first reading: %d   <- read through the old pointer\n", *first);

    free(log.data);
    return 0;
}
