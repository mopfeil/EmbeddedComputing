/* config.c - why does it crash? (JSLinux, Alpine x86_64)
 * gcc -g -O0 -o config config.c && ./config
 */
#include <stdio.h>
#include <string.h>

struct setting { const char *key; int value; };

static struct setting settings[] = {
    {"rate", 100}, {"threshold", 42}, {NULL, 0}
};

struct setting *find(const char *key) {
    for (struct setting *s = settings; s->key != NULL; s++)
        if (strcmp(s->key, key) == 0)
            return s;
    return NULL;                      /* key not found */
}

int main(void) {
    printf("rate      = %d\n", find("rate")->value);
    printf("threshold = %d\n", find("threshold")->value);
    printf("limit     = %d\n", find("limit")->value);
    return 0;
}
