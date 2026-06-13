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



// --- LOADER ERROR ENUM ---

enum class LoaderError {
    OK,
    INVALID_ARGUMENT,
    UNSUPPORTED_TYPE,
    UNSAFE_INTEGER,
    EMBEDDED_NUL,
    INVALID_UTF8,
    DUPLICATE_KEY,
    UNSUPPORTED_VECTOR_FIELD,
    SERIALIZE_ERROR,
    MEMORY_ERROR
};

// --- LOADER IMPLEMENTATION (Test-only) ---


static bool is_valid_utf8_string(const std::string& str) {
    const unsigned char* p = reinterpret_cast<const unsigned char*>(str.data());
    size_t len = str.size();
    size_t i = 0;
    while (i < len) {
        unsigned char c = p[i];
        int extra = 0;
        uint32_t min_cp = 0;
        if (c < 0x80) {
            i++;
            continue;
        } else if ((c & 0xE0) == 0xC0) {
            extra = 1; min_cp = 0x80;
        } else if ((c & 0xF0) == 0xE0) {
            extra = 2; min_cp = 0x800;
        } else if ((c & 0xF8) == 0xF0) {
            extra = 3; min_cp = 0x10000;
        } else {
            return false;
        }
        if (i + extra >= len) return false;
        uint32_t cp = c & (0xFF >> (extra + 1));
        for (int j = 1; j <= extra; ++j) {
            if ((p[i + j] & 0xC0) != 0x80) return false;
            cp = (cp << 6) | (p[i + j] & 0x3F);
        }
        if (cp < min_cp) return false; // Overlong encoding
        if (cp > 0x10FFFF) return false;
        if (cp >= 0xD800 && cp <= 0xDFFF) return false; // Surrogates are invalid UTF-8
        i += extra + 1;
    }
    return true;
}

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
            if (input->integer_val < -9007199254740991LL || input->integer_val > 9007199254740991LL) {
                return LoaderError::UNSAFE_INTEGER;
            }
            auto res = ModelValue::make_integer(input->integer_val);
            if (res.error == ModelError::UNSAFE_INTEGER) return LoaderError::UNSAFE_INTEGER;
            if (res.error != ModelError::OK) return LoaderError::MEMORY_ERROR;
            output = std::move(res.value);
            return LoaderError::OK;
        }
        case JsonType::STRING: {
            if (input->string_val.find('\0') != std::string::npos) {
                return LoaderError::EMBEDDED_NUL;
            }
            if (!is_valid_utf8_string(input->string_val)) {
                return LoaderError::INVALID_UTF8;
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
                if (member.key.find('\0') != std::string::npos) {
                    return LoaderError::EMBEDDED_NUL;
                }
                if (!is_valid_utf8_string(member.key)) {
                    return LoaderError::INVALID_UTF8;
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

#include "generated_jcs_positive_loader_fixtures.hpp"


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

    // Object containing array
    JsonNode arr_elem1; arr_elem1.type = JsonType::INTEGER; arr_elem1.integer_val = 42;
    JsonNode arr_node; arr_node.type = JsonType::ARRAY; arr_node.array_elements.push_back(&arr_elem1);
    JsonNode obj_arr_node; obj_arr_node.type = JsonType::OBJECT; obj_arr_node.object_members.push_back({"arr", &arr_node});
    failures += run_positive_test("object containing array", &obj_arr_node, "{\"arr\":[42]}", "7b22617272223a5b34325d7d");

    // Array containing object
    JsonNode inner_obj; inner_obj.type = JsonType::OBJECT; inner_obj.object_members.push_back({"k", &bool_node});
    JsonNode arr_obj_node; arr_obj_node.type = JsonType::ARRAY; arr_obj_node.array_elements.push_back(&inner_obj);
    failures += run_positive_test("array containing object", &arr_obj_node, "[{\"k\":true}]", "5b7b226b223a747275657d5d");


    // --- MANUAL HARDENING ADD-ONS ---
    JsonNode empty_str_node;
    empty_str_node.type = JsonType::STRING;
    empty_str_node.string_val = "";
    failures += run_positive_test("empty string", &empty_str_node, "\"\"", "2222");

    JsonNode empty_key_obj;
    empty_key_obj.type = JsonType::OBJECT;
    empty_key_obj.object_members.push_back({"", &bool_node});
    failures += run_positive_test("empty object key", &empty_key_obj, "{\"\":true}", "7b22223a747275657d");

    JsonNode invalid_utf8_trunc;
    invalid_utf8_trunc.type = JsonType::STRING;
    invalid_utf8_trunc.string_val = "\xe2\x98";
    failures += run_negative_test("invalid utf8 (truncated)", &invalid_utf8_trunc, LoaderError::INVALID_UTF8);

    JsonNode invalid_utf8_surrogate;
    invalid_utf8_surrogate.type = JsonType::STRING;
    invalid_utf8_surrogate.string_val = "\xed\xa0\x80";
    failures += run_negative_test("invalid utf8 (surrogate encoded in UTF-8)", &invalid_utf8_surrogate, LoaderError::INVALID_UTF8);

    JsonNode invalid_utf8_toolarge;
    invalid_utf8_toolarge.type = JsonType::STRING;
    invalid_utf8_toolarge.string_val = "\xf4\x90\x80\x80";
    failures += run_negative_test("invalid utf8 (code point above U+10FFFF)", &invalid_utf8_toolarge, LoaderError::INVALID_UTF8);

    // --- GENERATED FIXTURES ---
    generated_jcs_fixtures_init();
    for (size_t i = 0; i < generated_jcs_vectors_count; i++) {
        const GeneratedJcsVector* vec = generated_jcs_vectors[i];
        failures += run_positive_test(vec->name, vec->input, vec->expected_string, vec->expected_hex);
    }

    // --- NEGATIVE TESTS ---

    // 1. Unsupported float
    JsonNode neg_float;
    neg_float.type = JsonType::UNSUPPORTED_FLOAT;
    failures += run_negative_test("unsupported float", &neg_float, LoaderError::UNSUPPORTED_TYPE);

    // 2. Unsafe integer
    JsonNode neg_unsafe_int;
    neg_unsafe_int.type = JsonType::UNSAFE_INTEGER;
    failures += run_negative_test("unsafe integer sentinel", &neg_unsafe_int, LoaderError::UNSAFE_INTEGER);

    JsonNode neg_int_above; neg_int_above.type = JsonType::INTEGER; neg_int_above.integer_val = 9007199254740992LL;
    failures += run_negative_test("ordinary integer above safe max", &neg_int_above, LoaderError::UNSAFE_INTEGER);

    JsonNode neg_int_below; neg_int_below.type = JsonType::INTEGER; neg_int_below.integer_val = -9007199254740992LL;
    failures += run_negative_test("ordinary integer below safe min", &neg_int_below, LoaderError::UNSAFE_INTEGER);

    // 3. Embedded NUL in string
    JsonNode neg_nul_str;
    neg_nul_str.type = JsonType::STRING;
    neg_nul_str.string_val = std::string("bad\0string", 10);
    failures += run_negative_test("embedded NUL in string", &neg_nul_str, LoaderError::EMBEDDED_NUL);

    JsonNode neg_nul_key;
    neg_nul_key.type = JsonType::OBJECT;
    neg_nul_key.object_members.push_back({std::string("bad\0key", 7), &val1});
    failures += run_negative_test("embedded NUL in key", &neg_nul_key, LoaderError::EMBEDDED_NUL);

    JsonNode neg_utf8_str;
    neg_utf8_str.type = JsonType::STRING;
    neg_utf8_str.string_val = "\xFF\xFE";
    failures += run_negative_test("invalid UTF-8 in string", &neg_utf8_str, LoaderError::INVALID_UTF8);

    JsonNode neg_utf8_key;
    neg_utf8_key.type = JsonType::OBJECT;
    neg_utf8_key.object_members.push_back({"\xC0\x80", &val1}); // Overlong encoding of NUL
    failures += run_negative_test("invalid UTF-8 in key", &neg_utf8_key, LoaderError::INVALID_UTF8);

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
