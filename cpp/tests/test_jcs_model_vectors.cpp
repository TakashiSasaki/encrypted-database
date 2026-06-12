#include "vault_jcs_model.hpp"
#include "vault_jcs_internal.h"
#include "generated_jcs_vectors.h"
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>
#include <sstream>

using namespace vault::jcs;

/*
 * Generated-Fixture Bridge Documentation:
 *
 * This bridge acts purely as a generated-fixture converter.
 * - It reuses 'generated_jcs_vectors.h' from the generator output.
 * - It converts generated-AST 'VaultJcsValue' values into C++ parser-free 'ModelValue' values.
 * - It DOES NOT parse raw JSON.
 * - It DOES NOT load JSON vector files at runtime.
 * - It DOES NOT consume 'future-boundary-plan.json'.
 * - It DOES NOT prove full RFC 8785 generic JCS conformance.
 * - It DOES NOT cover future UTF-16 key-ordering vectors.
 */

// Implementation will follow.

static Result<ModelValue> convert_generated_to_model(const VaultJcsValue* input) {
    if (!input) {
        return Result<ModelValue>::err(ModelError::INVALID_ARG);
    }

    switch (input->type) {
        case VAULT_JCS_NULL:
            return ModelValue::make_null();
        case VAULT_JCS_BOOLEAN:
            return ModelValue::make_boolean(input->value.boolean_val);
        case VAULT_JCS_INTEGER:
            return ModelValue::make_integer(input->value.integer_val);
        case VAULT_JCS_STRING:
            return ModelValue::make_string(std::string(input->value.string_val));
        case VAULT_JCS_ARRAY: {
            ArrayValue elements;
            elements.reserve(input->value.array.count);
            for (size_t i = 0; i < input->value.array.count; ++i) {
                auto res = convert_generated_to_model(input->value.array.elements[i]);
                if (res.error != ModelError::OK) {
                    return res;
                }
                elements.push_back(std::move(res.value));
            }
            return ModelValue::make_array(std::move(elements));
        }
        case VAULT_JCS_OBJECT: {
            ObjectValue members;
            members.reserve(input->value.object.count);
            for (size_t i = 0; i < input->value.object.count; ++i) {
                auto res = convert_generated_to_model(input->value.object.members[i].value);
                if (res.error != ModelError::OK) {
                    return res;
                }
                members.emplace_back(std::string(input->value.object.members[i].key), std::move(res.value));
            }
            return ModelValue::make_object(std::move(members));
        }
        default:
            return Result<ModelValue>::err(ModelError::INVALID_ARG);
    }
}

static std::string bytes_to_hex(const std::string& input) {
    std::ostringstream oss;
    for (unsigned char c : input) {
        oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(c);
    }
    return oss.str();
}

static int run_vector_test(const JcsTestVector& vector) {
    std::cout << "Running vault_jcs_model vector test: " << vector.name << "\n";

    auto res = convert_generated_to_model(vector.input);
    if (res.error != ModelError::OK) {
        std::cout << "  FAIL: conversion failed with error " << static_cast<int>(res.error) << "\n";
        return 1;
    }

    auto ser_res = res.value.serialize();
    if (ser_res.error != ModelError::OK) {
        std::cout << "  FAIL: serialize failed with error " << static_cast<int>(ser_res.error) << "\n";
        return 1;
    }

    const std::string& output = ser_res.value;
    std::string hex_output = bytes_to_hex(output);

    if (output != vector.expected_string) {
        std::cout << "  FAIL: string mismatch\n";
        std::cout << "    Expected: " << vector.expected_string << "\n";
        std::cout << "    Got:      " << output << "\n";
        return 1;
    }

    if (hex_output != vector.expected_hex) {
        std::cout << "  FAIL: hex mismatch\n";
        std::cout << "    Expected: " << vector.expected_hex << "\n";
        std::cout << "    Got:      " << hex_output << "\n";
        return 1;
    }

    std::cout << "  PASS\n";
    return 0;
}

int main() {
    std::cout << "Running vault_jcs_model_vectors tests from shared generated vectors...\n";
    int failures = 0;

    if (NUM_JCS_TEST_VECTORS <= 0) {
        std::cout << "FAIL: No vectors found.\n";
        return 1;
    }

    for (int i = 0; i < NUM_JCS_TEST_VECTORS; i++) {
        failures += run_vector_test(JCS_TEST_VECTORS[i]);
    }

    if (failures == 0) {
        std::cout << "All vault_jcs_model_vectors tests passed.\n";
        return 0;
    } else {
        std::cout << failures << " vault_jcs_model_vectors tests failed.\n";
        return 1;
    }
}
