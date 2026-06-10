#include <stdio.h>
#include <string.h>
#include "vault_content_type_internal.h"

int main(void) {
    int failures = 0;

    struct {
        const char* name;
        const char* content_type;
        size_t len;
        int expected;
    } test_cases[] = {
        {"valid json", "application/json", 16, 1},
        {"valid octet-stream", "application/octet-stream", 24, 1},
        {"valid text", "text/plain", 10, 1},
        {"valid mixed case (no normalize)", "Application/JSON", 16, 1},
        {"valid minimal", "x/y", 3, 1},
        {"valid with parameter", "application/example; note=\"x\"", 29, 1},
        {"valid with leading space (no trim)", " application/json", 17, 1},
        {"valid with trailing space (no trim)", "application/json ", 17, 1},
        {"null", NULL, 0, 0},
        {"empty", "", 0, 0},
        {"missing slash", "application", 11, 0},
        {"missing type", "/json", 5, 0},
        {"missing subtype", "application/", 12, 0},
        {"multiple slashes", "application/json/extra", 22, 0},
        {"newline char", "application\n/json", 17, 0},
        {"tab char", "application\t/json", 17, 0},
        {"del char", "application/json\x7f", 17, 0},
        {"control char SOH", "application\x01/json", 17, 0},
        {"only spaces", "   ", 3, 0},
        {"spaces around slash", " / ", 3, 1}, // valid under our minimal rule: type=" ", subtype=" "
        {"embedded NUL", "application/json\0\n", 18, 0}
    };

    printf("Running Content-Type syntax validation tests...\n");
    for (size_t i = 0; i < sizeof(test_cases) / sizeof(test_cases[0]); ++i) {
        int actual = vault_is_valid_content_type(test_cases[i].content_type, test_cases[i].len);
        if (actual != test_cases[i].expected) {
            printf("FAIL: Test '%s' expected %d, got %d for '%s'\n",
                   test_cases[i].name, test_cases[i].expected, actual,
                   test_cases[i].content_type ? test_cases[i].content_type : "(null)");
            failures++;
        }
    }

    if (failures == 0) {
        printf("All Content-Type tests passed.\n");
        return 0;
    } else {
        printf("%d Content-Type test(s) failed.\n", failures);
        return 1;
    }
}
