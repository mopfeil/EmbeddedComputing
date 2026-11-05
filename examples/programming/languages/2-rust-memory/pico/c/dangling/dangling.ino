/*
 * The dangling pointer of ../../c/dangling.c on the Raspberry Pi Pico.
 *
 * A data logger stores readings in a buffer that grows when it is full.
 * The program keeps a pointer to the first reading. Meanwhile another
 * part of the firmware allocates a message buffer, so the log cannot grow
 * in place: realloc() moves it and frees the old block. The pointer now
 * points into freed memory, which the next malloc() hands out again.
 *
 * On the microcontroller there is no AddressSanitizer and no operating
 * system that stops the program: it silently continues with a wrong value.
 * Here that value decides whether an alarm is raised.
 *
 * Board: Raspberry Pi Pico (arduino-pico core), Wokwi. Output on Serial1.
 */
#include <Arduino.h>
#include <stdlib.h>
#include <string.h>

typedef struct {
    int16_t *data;
    size_t len, cap;
} Log;

static void log_push(Log *log, int16_t value)
{
    if (log->len == log->cap) {                   // full: grow the buffer
        log->cap = log->cap ? 2 * log->cap : 4;
        log->data = (int16_t *)realloc(log->data, log->cap * sizeof *log->data);
        if (!log->data)
            panic("out of memory");
    }
    log->data[log->len++] = value;
}

void setup()
{
    Serial1.begin(115200);
    Log log = {0};
    log_push(&log, 215);                          // 21.5 degC, in 0.1 degC

    int16_t *first = &log.data[0];                // remember the first reading
    Serial1.printf("first reading: %d (address %p)\n", *first, first);

    char *msg = (char *)malloc(32);               // another part of the firmware
    strcpy(msg, "logger running");                //   allocates a message buffer
    Serial1.printf("%s, message at %p\n", msg, msg);
    for (int i = 0; i < 100; i++)                 // more readings: buffer grows
        log_push(&log, (int16_t)(220 + i));
    char *report = (char *)malloc(8);             // gets the freed block
    strcpy(report, "OK");                         //   and writes "OK" into it

    Serial1.printf("buffer is now at        %p\n", log.data);
    Serial1.printf("first reading: %d   <- read through the old pointer (0x%04X = \"%c%c\")\n",
                   *first, (uint16_t)*first, ((char *)first)[0], ((char *)first)[1]);
    Serial1.printf("alarm (first reading > 30.0 degC): %s\n", *first > 300 ? "YES" : "no");

    free(report);
    free(msg);
    free(log.data);
}

void loop() {}
