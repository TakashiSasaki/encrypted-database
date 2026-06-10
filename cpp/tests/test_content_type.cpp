#include <iostream>
#include <string>
#include <string_view>
#include "vault_content_type_internal.hpp"

struct TestCase {
    std::string name;
    std::string_view content_type;
    bool expected;
};

int main() {
    int failures = 0;

    TestCase test_cases[] = {
        {"valid json", std::string_view("application/json", 16), true},
        {"valid octet-stream", std::string_view("application/octet-stream", 24), true},
        {"valid text", std::string_view("text/plain", 10), true},
        {"valid mixed case (no normalize)", std::string_view("Application/JSON", 16), true},
        {"valid minimal", std::string_view("x/y", 3), true},
        {"valid with parameter", std::string_view("application/example; note=\"x\"", 29), true},
        {"valid with leading space (no trim)", std::string_view(" application/json", 17), true},
        {"valid with trailing space (no trim)", std::string_view("application/json ", 17), true},
        {"empty", std::string_view("", 0), false},
        {"missing slash", std::string_view("application", 11), false},
        {"missing type", std::string_view("/json", 5), false},
        {"missing subtype", std::string_view("application/", 12), false},
        {"multiple slashes", std::string_view("application/json/extra", 22), false},
        {"newline char", std::string_view("application\n/json", 17), false},
        {"tab char", std::string_view("application\t/json", 17), false},
        {"del char", std::string_view("application/json\x7f", 17), false},
        {"control char SOH", std::string_view("application\x01/json", 17), false},
        {"only spaces", std::string_view("   ", 3), false},
        {"spaces around slash", std::string_view(" / ", 3), true}, // valid under our minimal rule: type=" ", subtype=" "
        {"embedded NUL", std::string_view("application/json\0\n", 18), false}
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
