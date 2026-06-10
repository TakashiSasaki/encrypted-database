#include <stdio.h>
#include "vault_content_type_internal.h"

int main(void) {
    int failures = 0;

    struct {
        const char* name;
        const char* content_type;
        int expected;
    } test_cases[] = {
        {"valid json", "application/json", 1},
        {"valid octet-stream", "application/octet-stream", 1},
        {"valid text", "text/plain", 1},
        {"valid mixed case (no normalize)", "Application/JSON", 1},
        {"valid minimal", "x/y", 1},
        {"valid with parameter", "application/example; note=\"x\"", 1},
        {"valid with leading space (no trim)", " application/json", 1},
        {"valid with trailing space (no trim)", "application/json ", 1},
        {"null", NULL, 0},
        {"empty", "", 0},
        {"missing slash", "application", 0},
        {"missing type", "/json", 0},
        {"missing subtype", "application/", 0},
        {"multiple slashes", "application/json/extra", 0},
        {"newline char", "application\n/json", 0},
        {"tab char", "application\t/json", 0},
        {"del char", "application/json\x7f", 0},
        {"control char SOH", "application\x01/json", 0},
        {"only spaces", "   ", 0},
        {"spaces around slash", " / ", 1} // valid under our minimal rule: type=" ", subtype=" "
    };

    printf("Running Content-Type syntax validation tests...\n");
    for (size_t i = 0; i < sizeof(test_cases) / sizeof(test_cases[0]); ++i) {
        int actual = vault_is_valid_content_type(test_cases[i].content_type);
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
