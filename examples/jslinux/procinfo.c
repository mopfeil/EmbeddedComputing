/* procinfo.c - a tiny monitoring tool (JSLinux, Buildroot RISC-V)
 * gcc -g -O1 -o procinfo procinfo.c && ./procinfo
 * Something is wrong with the uptime. Find out what with: strace ./procinfo
 */
#include <stdio.h>
#include <stdint.h>

/* read the first number of a text file, 0 if the file cannot be read */
double read_number(const char *path) {
    double v = 0;
    FILE *f = fopen(path, "r");
    if (f) {
        if (fscanf(f, "%lf", &v) != 1)
            v = 0;
        fclose(f);
    }
    return v;
}

/* the function of chapter Processors - look at it with objdump */
uint32_t sum16(const uint16_t *a, int n) {
    uint32_t s = 0;
    for (int i = 0; i < n; i++)
        s += a[i];
    return s;
}

int main(void) {
    const uint16_t values[] = {1, 2, 3, 1000, 60000, 65535};
    printf("uptime: %.0f s\n", read_number("/proc/uptme"));
    printf("load:   %.2f\n", read_number("/proc/loadavg"));
    printf("sum:    %u\n", sum16(values, 6));
    return 0;
}
