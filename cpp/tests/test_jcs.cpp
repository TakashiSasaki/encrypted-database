#include "vault_jcs_internal.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>
#include <sstream>

#include "generated_jcs_vectors.h"

static std::string hex_encode(const std::string& data) {
    std::ostringstream oss;
    for (unsigned char c : data) {
        oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(c);
    }
    return oss.str();
}

static int run_vector_test(const JcsTestVector& vector) {
    std::cout << "Running JCS vector test: " << vector.name << "\n";

    std::string serialized = vault::jcs::serialize_generated_value(*vector.input);

    if (serialized != vector.expected_string) {
        std::cout << "  FAIL: string mismatch\n";
        std::cout << "    Expected: " << vector.expected_string << "\n";
        std::cout << "    Got     : " << serialized << "\n";
        return 1;
    }

    std::string hex = hex_encode(serialized);
    if (hex != vector.expected_hex) {
        std::cout << "  FAIL: hex mismatch\n";
        std::cout << "    Expected: " << vector.expected_hex << "\n";
        std::cout << "    Got     : " << hex << "\n";
        return 1;
    }

    std::cout << "  PASS\n";
    return 0;
}

static int run_local_regression_test() {
    std::cout << "Running local regression test for boolean/null...\n";

    // Create a local AST: {"b":false,"n":null,"t":true}
    static const VaultJcsValue node_false = { VAULT_JCS_BOOLEAN, { .boolean_val = false } };
    static const VaultJcsValue node_null = { VAULT_JCS_NULL, {0} };
    static const VaultJcsValue node_true = { VAULT_JCS_BOOLEAN, { .boolean_val = true } };

    // Deliberately unsorted keys to test sorting
    static const VaultJcsObjectMember members[] = {
        { "t", &node_true },
        { "b", &node_false },
        { "n", &node_null }
    };
    static const VaultJcsValue root = { VAULT_JCS_OBJECT, { .object = { members, 3 } } };

    std::string expected = "{\"b\":false,\"n\":null,\"t\":true}";
    std::string serialized = vault::jcs::serialize_generated_value(root);

    if (serialized != expected) {
        std::cout << "  FAIL: boolean/null local regression mismatch\n";
        std::cout << "    Expected: " << expected << "\n";
        std::cout << "    Got     : " << serialized << "\n";
        return 1;
    }

    std::cout << "  PASS\n";
    return 0;
}

int main() {
    int failures = 0;

    for (int i = 0; i < NUM_JCS_TEST_VECTORS; i++) {
        failures += run_vector_test(JCS_TEST_VECTORS[i]);
    }

    failures += run_local_regression_test();

    if (failures > 0) {
        std::cout << failures << " tests failed.\n";
        return 1;
    }

    std::cout << "All JCS tests passed.\n";
    return 0;
}
