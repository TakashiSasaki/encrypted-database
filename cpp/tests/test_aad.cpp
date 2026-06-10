#include <iostream>
#include <string>
#include <iomanip>
#include <sstream>
#include "vault_aad_internal.hpp"
#include "generated_aad_vectors.h"

std::string to_hex(const std::string& input) {
    std::ostringstream oss;
    for (unsigned char c : input) {
        oss << std::hex << std::setw(2) << std::setfill('0') << (int)c;
    }
    return oss.str();
}

int main() {
    int failures = 0;

    std::cout << "Running AAD vector tests...\n";

    for (int i = 0; i < NUM_AAD_TEST_VECTORS; ++i) {
        const AadTestVector& v = AAD_TEST_VECTORS[i];
        std::string actual_string;

        std::string policy = v.policy ? v.policy : "";
        if (policy == "record-payload-v1") {
            actual_string = vault::aad::record_payload_v1(v.object_uuid, v.schema_uuid, v.content_type, v.kid, v.alg);
        } else if (policy == "wrap-database-key-v1") {
            actual_string = vault::aad::wrap_database_key_v1(v.wrapped_kid, v.wrapping_kid);
        } else if (policy == "wrap-record-key-v1") {
            actual_string = vault::aad::wrap_record_key_v1(v.wrapped_kid, v.wrapping_kid);
        } else {
            std::cerr << "FAIL: Unknown policy '" << policy << "' for vector '" << v.name << "'\n";
            failures++;
            continue;
        }

        std::string expected_string = v.expected_string ? v.expected_string : "";
        if (actual_string != expected_string) {
            std::cerr << "FAIL: String mismatch for vector '" << v.name << "'\n"
                      << "  Expected: " << expected_string << "\n"
                      << "  Actual  : " << actual_string << "\n";
            failures++;
            continue;
        }

        std::string actual_hex = to_hex(actual_string);
        std::string expected_hex = v.expected_hex ? v.expected_hex : "";

        if (actual_hex != expected_hex) {
            std::cerr << "FAIL: Hex mismatch for vector '" << v.name << "'\n"
                      << "  Expected: " << expected_hex << "\n"
                      << "  Actual  : " << actual_hex << "\n";
            failures++;
        }
    }

    if (failures == 0) {
        std::cout << "All AAD vector tests passed.\n";
        return 0;
    } else {
        std::cerr << failures << " AAD vector test(s) failed.\n";
        return 1;
    }
}
