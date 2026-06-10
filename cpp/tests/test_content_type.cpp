#include <iostream>
#include <string>
#include "vault_content_type_internal.hpp"

struct TestCase {
    std::string name;
    std::string content_type;
    bool expected;
};

int main() {
    int failures = 0;

    TestCase test_cases[] = {
        {"valid json", "application/json", true},
        {"valid octet-stream", "application/octet-stream", true},
        {"valid text", "text/plain", true},
        {"valid mixed case (no normalize)", "Application/JSON", true},
        {"valid minimal", "x/y", true},
        {"valid with parameter", "application/example; note=\"x\"", true},
        {"valid with leading space (no trim)", " application/json", true},
        {"valid with trailing space (no trim)", "application/json ", true},
        {"empty", "", false},
        {"missing slash", "application", false},
        {"missing type", "/json", false},
        {"missing subtype", "application/", false},
        {"multiple slashes", "application/json/extra", false},
        {"newline char", "application\n/json", false},
        {"tab char", "application\t/json", false},
        {"del char", "application/json\x7f", false},
        {"control char SOH", "application\x01/json", false},
        {"only spaces", "   ", false},
        {"spaces around slash", " / ", true} // valid under our minimal rule: type=" ", subtype=" "
    };

    std::cout << "Running Content-Type syntax validation tests...\n";
    for (const auto& tc : test_cases) {
        bool actual = vault::content_type::is_valid(tc.content_type);
        if (actual != tc.expected) {
            std::cerr << "FAIL: Test '" << tc.name << "' expected " << tc.expected
                      << ", got " << actual << " for '" << tc.content_type << "'\n";
            failures++;
        }
    }

    if (failures == 0) {
        std::cout << "All Content-Type tests passed.\n";
        return 0;
    } else {
        std::cerr << failures << " Content-Type test(s) failed.\n";
        return 1;
    }
}
