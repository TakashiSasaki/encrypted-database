#include "vault_jcs_model.hpp"
#include <iostream>
#include <string>
#include <vector>
#include <iomanip>
#include <sstream>

using namespace vault::jcs;

// --- TEST-HARNESS GENERIC JSON REPRESENTATION ---

namespace vault {
namespace jcs {
namespace test {

enum class JsonType {
    NULL_VAL,
    BOOLEAN,
    INTEGER,
    STRING,
    ARRAY,
    OBJECT,

    // Sentinels for negative tests
    UNSUPPORTED_FLOAT,
    UNSAFE_INTEGER,
    RAW_JSON,
    REJECTION_META,
    UNKNOWN_META
};

struct JsonNode;

struct ObjectMember {
    std::string key;
    JsonNode* value;
};

struct JsonNode {
    JsonType type;

    bool boolean_val = false;
    int64_t integer_val = 0;
    std::string string_val;

    std::vector<JsonNode*> array_elements;

    std::vector<ObjectMember> object_members;
    bool has_duplicates = false;
};

// --- LOADER ERROR ENUM ---

enum class LoaderError {
    OK,
    INVALID_ARGUMENT,
    UNSUPPORTED_TYPE,
    UNSAFE_INTEGER,
    EMBEDDED_NUL,
    DUPLICATE_KEY,
    UNSUPPORTED_VECTOR_FIELD,
    SERIALIZE_ERROR,
    MEMORY_ERROR
};

// --- LOADER IMPLEMENTATION (Test-only) ---

static LoaderError convert_test_to_model(const JsonNode* input, ModelValue& output) {
    if (!input) return LoaderError::INVALID_ARGUMENT;

    switch (input->type) {
        case JsonType::NULL_VAL: {
            auto res = ModelValue::make_null();
            if (res.error != ModelError::OK) return LoaderError::MEMORY_ERROR;
            output = std::move(res.value);
            return LoaderError::OK;
        }
        case JsonType::BOOLEAN: {
            auto res = ModelValue::make_boolean(input->boolean_val);
            if (res.error != ModelError::OK) return LoaderError::MEMORY_ERROR;
            output = std::move(res.value);
            return LoaderError::OK;
        }
        case JsonType::INTEGER: {
            auto res = ModelValue::make_integer(input->integer_val);
            if (res.error != ModelError::OK) return LoaderError::MEMORY_ERROR;
            output = std::move(res.value);
            return LoaderError::OK;
        }
        case JsonType::STRING: {
            if (input->string_val.find("HAS_NUL_SENTINEL") != std::string::npos) {
                return LoaderError::EMBEDDED_NUL;
            }
            auto res = ModelValue::make_string(input->string_val);
            if (res.error != ModelError::OK) return LoaderError::MEMORY_ERROR;
            output = std::move(res.value);
            return LoaderError::OK;
        }
        case JsonType::ARRAY: {
            ArrayValue elements;
            elements.reserve(input->array_elements.size());
            for (const auto* elem : input->array_elements) {
                ModelValue elem_val;
                LoaderError err = convert_test_to_model(elem, elem_val);
                if (err != LoaderError::OK) return err;
                elements.push_back(std::move(elem_val));
            }
            auto res = ModelValue::make_array(std::move(elements));
            if (res.error != ModelError::OK) return LoaderError::MEMORY_ERROR;
            output = std::move(res.value);
            return LoaderError::OK;
        }
        case JsonType::OBJECT: {
            if (input->has_duplicates) {
                return LoaderError::DUPLICATE_KEY;
            }
            ObjectValue members;
            members.reserve(input->object_members.size());
            for (const auto& member : input->object_members) {
                if (member.key.find("HAS_NUL_SENTINEL") != std::string::npos) {
                    return LoaderError::EMBEDDED_NUL;
                }
                ModelValue member_val;
                LoaderError err = convert_test_to_model(member.value, member_val);
                if (err != LoaderError::OK) return err;
                members.emplace_back(member.key, std::move(member_val));
            }
            auto res = ModelValue::make_object(std::move(members));
            if (res.error != ModelError::OK) return LoaderError::MEMORY_ERROR;
            output = std::move(res.value);
            return LoaderError::OK;
        }
        case JsonType::UNSUPPORTED_FLOAT:
            return LoaderError::UNSUPPORTED_TYPE;
        case JsonType::UNSAFE_INTEGER:
            return LoaderError::UNSAFE_INTEGER;
        case JsonType::RAW_JSON:
        case JsonType::REJECTION_META:
        case JsonType::UNKNOWN_META:
            return LoaderError::UNSUPPORTED_VECTOR_FIELD;
        default:
            return LoaderError::UNSUPPORTED_TYPE;
    }
}

} // namespace test
} // namespace jcs
} // namespace vault

using namespace vault::jcs::test;

// --- TEST UTILS ---

static std::string bytes_to_hex(const std::string& input) {
    std::ostringstream oss;
    for (unsigned char c : input) {
        oss << std::hex << std::setw(2) << std::setfill('0') << static_cast<int>(c);
    }
    return oss.str();
}

static int run_positive_test(const std::string& name, const JsonNode* input, const std::string& expected_string, const std::string& expected_hex) {
    std::cout << "Running C++ positive loader test: " << name << "\n";

    ModelValue v;
    LoaderError err = convert_test_to_model(input, v);
    if (err != LoaderError::OK) {
        std::cout << "  FAIL: conversion failed with error " << static_cast<int>(err) << "\n";
        return 1;
    }

    auto ser_res = v.serialize();
    if (ser_res.error != ModelError::OK) {
        std::cout << "  FAIL: serialize failed with error " << static_cast<int>(ser_res.error) << "\n";
        return 1;
    }

    const std::string& output = ser_res.value;
    std::string hex_output = bytes_to_hex(output);

    if (output != expected_string) {
        std::cout << "  FAIL: string mismatch\n    Expected: " << expected_string << "\n    Got:      " << output << "\n";
        return 1;
    }

    if (hex_output != expected_hex) {
        std::cout << "  FAIL: hex mismatch\n    Expected: " << expected_hex << "\n    Got:      " << hex_output << "\n";
        return 1;
    }

    std::cout << "  PASS\n";
    return 0;
}

static int run_negative_test(const std::string& name, const JsonNode* input, LoaderError expected_err) {
    std::cout << "Running C++ negative loader test: " << name << "\n";

    ModelValue v;
    LoaderError err = convert_test_to_model(input, v);
    if (err == expected_err) {
        std::cout << "  PASS (got expected error " << static_cast<int>(err) << ")\n";
        return 0;
    } else {
        std::cout << "  FAIL: expected error " << static_cast<int>(expected_err) << ", got " << static_cast<int>(err) << "\n";
        return 1;
    }
}

// --- TEST CASES ---

int main() {
    int failures = 0;

    // --- POSITIVE TESTS ---

    // 1. Empty Object
    JsonNode empty_obj;
    empty_obj.type = JsonType::OBJECT;
    failures += run_positive_test("empty object", &empty_obj, "{}", "7b7d");

    // 2. Empty Array
    JsonNode empty_arr;
    empty_arr.type = JsonType::ARRAY;
    failures += run_positive_test("empty array", &empty_arr, "[]", "5b5d");

    // 3. String, Boolean, Null
    JsonNode str_node;
    str_node.type = JsonType::STRING;
    str_node.string_val = "hello";
    failures += run_positive_test("string", &str_node, "\"hello\"", "2268656c6c6f22");

    JsonNode bool_node;
    bool_node.type = JsonType::BOOLEAN;
    bool_node.boolean_val = true;
    failures += run_positive_test("boolean true", &bool_node, "true", "74727565");

    JsonNode null_node;
    null_node.type = JsonType::NULL_VAL;
    failures += run_positive_test("null", &null_node, "null", "6e756c6c");

    // 4. Safe Integer Min/Max
    JsonNode int_max;
    int_max.type = JsonType::INTEGER;
    int_max.integer_val = 9007199254740991LL;
    failures += run_positive_test("safe integer max", &int_max, "9007199254740991", "39303037313939323534373430393931");

    JsonNode int_min;
    int_min.type = JsonType::INTEGER;
    int_min.integer_val = -9007199254740991LL;
    failures += run_positive_test("safe integer min", &int_min, "-9007199254740991", "2d39303037313939323534373430393931");

    // 5. Nested objects/arrays and UTF-16 Surrogate key ordering
    JsonNode val1, val2;
    val1.type = JsonType::INTEGER; val1.integer_val = 1;
    val2.type = JsonType::INTEGER; val2.integer_val = 2;

    JsonNode nested_obj;
    nested_obj.type = JsonType::OBJECT;
    nested_obj.object_members.push_back({"\xEE\x80\x80", &val2});
    nested_obj.object_members.push_back({"\xF0\x90\x80\x80", &val1});

    failures += run_positive_test("utf-16 surrogate key ordering", &nested_obj,
        "{\"\xF0\x90\x80\x80\":1,\"\xEE\x80\x80\":2}",
        "7b22f0908080223a312c22ee8080223a327d");

    // --- NEGATIVE TESTS ---

    // 1. Unsupported float
    JsonNode neg_float;
    neg_float.type = JsonType::UNSUPPORTED_FLOAT;
    failures += run_negative_test("unsupported float", &neg_float, LoaderError::UNSUPPORTED_TYPE);

    // 2. Unsafe integer
    JsonNode neg_unsafe_int;
    neg_unsafe_int.type = JsonType::UNSAFE_INTEGER;
    failures += run_negative_test("unsafe integer", &neg_unsafe_int, LoaderError::UNSAFE_INTEGER);

    // 3. Embedded NUL in string
    JsonNode neg_nul_str;
    neg_nul_str.type = JsonType::STRING;
    neg_nul_str.string_val = "badHAS_NUL_SENTINELstring";
    failures += run_negative_test("embedded NUL in string", &neg_nul_str, LoaderError::EMBEDDED_NUL);

    // 4. Duplicate object key
    JsonNode neg_dup_key;
    neg_dup_key.type = JsonType::OBJECT;
    neg_dup_key.has_duplicates = true;
    neg_dup_key.object_members.push_back({"\xEE\x80\x80", &val2});
    neg_dup_key.object_members.push_back({"\xF0\x90\x80\x80", &val1});
    failures += run_negative_test("duplicate object key", &neg_dup_key, LoaderError::DUPLICATE_KEY);

    // 5. Raw JSON field
    JsonNode neg_raw_json;
    neg_raw_json.type = JsonType::RAW_JSON;
    failures += run_negative_test("raw json sentinel", &neg_raw_json, LoaderError::UNSUPPORTED_VECTOR_FIELD);

    // 6. Rejection/planning-only metadata
    JsonNode neg_rej_meta;
    neg_rej_meta.type = JsonType::REJECTION_META;
    failures += run_negative_test("rejection metadata", &neg_rej_meta, LoaderError::UNSUPPORTED_VECTOR_FIELD);

    // 7. Unknown metadata
    JsonNode neg_unk_meta;
    neg_unk_meta.type = JsonType::UNKNOWN_META;
    failures += run_negative_test("unknown metadata", &neg_unk_meta, LoaderError::UNSUPPORTED_VECTOR_FIELD);

    std::cout << "\nTotal failures: " << failures << "\n";
    return failures > 0 ? 1 : 0;
}
