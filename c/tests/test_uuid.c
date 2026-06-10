#include <stdio.h>
#include "vault_uuid_internal.h"

int main(void) {
    int failures = 0;

    struct {
        const char* name;
        const char* uuid;
        int expected;
    } test_cases[] = {
        {"valid v4", "12345678-1234-4234-8234-1234567890ab", 1},
        {"valid v7", "0188b488-8422-7945-8857-ab1234567890", 1},
        {"valid variant 9", "12345678-1234-4234-9234-1234567890ab", 1},
        {"valid variant a", "12345678-1234-4234-a234-1234567890ab", 1},
        {"valid variant b", "12345678-1234-4234-b234-1234567890ab", 1},
        {"valid version 1", "12345678-1234-1234-8234-1234567890ab", 1},
        {"valid version 8", "12345678-1234-8234-8234-1234567890ab", 1},
        {"null", NULL, 0},
        {"empty", "", 0},
        {"too short", "12345678-1234-4234-8234-1234567890a", 0},
        {"too long", "12345678-1234-4234-8234-1234567890abc", 0},
        {"uppercase", "12345678-1234-4234-8234-1234567890AB", 0},
        {"missing hyphen 1", "1234567891234-4234-8234-1234567890ab", 0},
        {"missing hyphen 2", "12345678-123454234-8234-1234567890ab", 0},
        {"missing hyphen 3", "12345678-1234-423458234-1234567890ab", 0},
        {"missing hyphen 4", "12345678-1234-4234-823451234567890ab", 0},
        {"invalid char", "12345678-1234-4234-8234-1234567890ag", 0},
        {"invalid version 0", "12345678-1234-0234-8234-1234567890ab", 0},
        {"invalid version 9", "12345678-1234-9234-8234-1234567890ab", 0},
        {"invalid version a", "12345678-1234-a234-8234-1234567890ab", 0},
        {"invalid variant 7", "12345678-1234-4234-7234-1234567890ab", 0},
        {"invalid variant c", "12345678-1234-4234-c234-1234567890ab", 0},
        {"hyphen instead of char", "12345678-1234-4234-8234--234567890ab", 0}
    };

    printf("Running UUID syntax validation tests...\n");
    for (size_t i = 0; i < sizeof(test_cases) / sizeof(test_cases[0]); ++i) {
        int actual = vault_is_valid_uuid(test_cases[i].uuid);
        if (actual != test_cases[i].expected) {
            printf("FAIL: Test '%s' expected %d, got %d for '%s'\n",
                   test_cases[i].name, test_cases[i].expected, actual,
                   test_cases[i].uuid ? test_cases[i].uuid : "(null)");
            failures++;
        }
    }

    if (failures == 0) {
        printf("All UUID tests passed.\n");
        return 0;
    } else {
        printf("%d UUID test(s) failed.\n", failures);
        return 1;
    }
}
