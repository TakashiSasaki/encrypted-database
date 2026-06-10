#include <iostream>
#include <string>
#include "vault_uuid_internal.hpp"

struct TestCase {
    std::string name;
    std::string uuid;
    bool expected;
};

int main() {
    int failures = 0;

    TestCase test_cases[] = {
        {"valid v4", "12345678-1234-4234-8234-1234567890ab", true},
        {"valid v7", "0188b488-8422-7945-8857-ab1234567890", true},
        {"valid variant 9", "12345678-1234-4234-9234-1234567890ab", true},
        {"valid variant a", "12345678-1234-4234-a234-1234567890ab", true},
        {"valid variant b", "12345678-1234-4234-b234-1234567890ab", true},
        {"valid version 1", "12345678-1234-1234-8234-1234567890ab", true},
        {"valid version 8", "12345678-1234-8234-8234-1234567890ab", true},
        {"empty", "", false},
        {"too short", "12345678-1234-4234-8234-1234567890a", false},
        {"too long", "12345678-1234-4234-8234-1234567890abc", false},
        {"uppercase", "12345678-1234-4234-8234-1234567890AB", false},
        {"missing hyphen 1", "1234567891234-4234-8234-1234567890ab", false},
        {"missing hyphen 2", "12345678-123454234-8234-1234567890ab", false},
        {"missing hyphen 3", "12345678-1234-423458234-1234567890ab", false},
        {"missing hyphen 4", "12345678-1234-4234-823451234567890ab", false},
        {"invalid char", "12345678-1234-4234-8234-1234567890ag", false},
        {"invalid version 0", "12345678-1234-0234-8234-1234567890ab", false},
        {"invalid version 9", "12345678-1234-9234-8234-1234567890ab", false},
        {"invalid version a", "12345678-1234-a234-8234-1234567890ab", false},
        {"invalid variant 7", "12345678-1234-4234-7234-1234567890ab", false},
        {"invalid variant c", "12345678-1234-4234-c234-1234567890ab", false},
        {"hyphen instead of char", "12345678-1234-4234-8234--234567890ab", false}
    };

    std::cout << "Running UUID syntax validation tests...\n";
    for (const auto& tc : test_cases) {
        bool actual = vault::uuid::is_valid(tc.uuid);
        if (actual != tc.expected) {
            std::cerr << "FAIL: Test '" << tc.name << "' expected " << tc.expected
                      << ", got " << actual << " for '" << tc.uuid << "'\n";
            failures++;
        }
    }

    if (failures == 0) {
        std::cout << "All UUID tests passed.\n";
        return 0;
    } else {
        std::cerr << failures << " UUID test(s) failed.\n";
        return 1;
    }
}
