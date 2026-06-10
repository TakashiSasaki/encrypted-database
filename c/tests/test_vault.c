#include <stdio.h>
#include <string.h>
#include "vault.h"

int main(void) {
    const char* expected = "vault c smoke test ok";
    const char* actual = vault_c_smoke_test();
    if (strcmp(actual, expected) != 0) {
        fprintf(stderr, "Expected \"%s\", got \"%s\"\n", expected, actual);
        return 1;
    }
    printf("Test passed.\n");
    return 0;
}
