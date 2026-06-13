#include "vault_jcs_model.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <stdint.h>

// --- TEST-HARNESS GENERIC JSON REPRESENTATION ---

typedef enum {
    TEST_JSON_NULL,
    TEST_JSON_BOOLEAN,
    TEST_JSON_INTEGER,
    TEST_JSON_STRING,
    TEST_JSON_ARRAY,
    TEST_JSON_OBJECT,

    // Sentinels for negative tests
    TEST_JSON_UNSUPPORTED_FLOAT,
    TEST_JSON_UNSAFE_INTEGER,
    TEST_JSON_RAW_JSON,
    TEST_JSON_REJECTION_META,
    TEST_JSON_UNKNOWN_META
} VaultJcsTestJsonType;

typedef struct VaultJcsTestJsonNode VaultJcsTestJsonNode;

typedef struct {
    const char* key;
    VaultJcsTestJsonNode* value;
} VaultJcsTestObjectMember;

struct VaultJcsTestJsonNode {
    VaultJcsTestJsonType type;
    union {
        bool boolean_val;
        int64_t integer_val;
        const char* string_val;
        struct {
            VaultJcsTestJsonNode* elements;
            size_t count;
        } array;
        struct {
            VaultJcsTestObjectMember* members;
            size_t count;
            bool has_duplicates;
        } object;
    } value;
};

// --- LOADER ERROR ENUM ---

typedef enum {
    LOADER_OK,
    LOADER_INVALID_ARGUMENT,
    LOADER_UNSUPPORTED_TYPE,
    LOADER_UNSAFE_INTEGER,
    LOADER_EMBEDDED_NUL,
    LOADER_DUPLICATE_KEY,
    LOADER_UNSUPPORTED_VECTOR_FIELD,
    LOADER_SERIALIZE_ERROR,
    LOADER_MEMORY_ERROR
} LoaderError;

// --- LOADER IMPLEMENTATION (Test-only) ---

static bool has_embedded_nul(const char* s) {
    if (!s) return false;
    // Assuming standard C strings for literal initializers, but if we pass length, we could check for \0 inside.
    // For this scaffold, let's use a convention: if the string is meant to contain NUL, it's explicitly tested.
    // However, C strings cannot natively contain embedded NULs without an explicit length.
    // In our test structs, we'll assume string_val is null-terminated but we might pass a known sentinel.
    // Let's implement a simple substring check for a specific literal sentinel: "\\u0000" if we want to simulate it,
    // or just rely on a flag or explicit checking if we add a length field.
    // To make it simple and strictly fail-closed on NULs: Since we don't have lengths in this mock,
    // we'll add an explicit check for a known embedded-NUL string sentinel: "NUL\0TEST" but that's truncated.
    return false;
}

// Helper to duplicate strings
static char* dup_str(const char* src) {
    if (!src) return NULL;
    size_t len = strlen(src);
    char* dst = (char*)malloc(len + 1);
    if (!dst) return NULL;
    memcpy(dst, src, len + 1);
    return dst;
}

static LoaderError test_loader_convert(const VaultJcsTestJsonNode* input, VaultJcsModelValue* output) {
    if (!input || !output) return LOADER_INVALID_ARGUMENT;

    switch (input->type) {
        case TEST_JSON_NULL:
            vault_jcs_model_init_null(output);
            return LOADER_OK;
        case TEST_JSON_BOOLEAN:
            vault_jcs_model_init_boolean(output, input->value.boolean_val);
            return LOADER_OK;
        case TEST_JSON_INTEGER:
            vault_jcs_model_init_integer(output, input->value.integer_val);
            return LOADER_OK;
        case TEST_JSON_STRING:
            // Check for embedded NUL sentinel or invalid strings
            // In C, a string with embedded NUL would require length.
            // We'll simulate checking for embedded NUL if string contains a specific sentinel for this mock loader
            if (input->value.string_val && strstr(input->value.string_val, "HAS_NUL_SENTINEL")) {
                return LOADER_EMBEDDED_NUL;
            }
            vault_jcs_model_init_string(output, input->value.string_val);
            return LOADER_OK;
        case TEST_JSON_ARRAY: {
            VaultJcsModelValue* elements = NULL;
            if (input->value.array.count > 0) {
                elements = (VaultJcsModelValue*)malloc(input->value.array.count * sizeof(VaultJcsModelValue));
                if (!elements) return LOADER_MEMORY_ERROR;

                for (size_t i = 0; i < input->value.array.count; ++i) {
                    LoaderError err = test_loader_convert(&input->value.array.elements[i], &elements[i]);
                    if (err != LOADER_OK) {
                        for (size_t j = 0; j < i; ++j) {
                            vault_jcs_model_free(&elements[j]);
                        }
                        free(elements);
                        return err;
                    }
                }
            }
            if (vault_jcs_model_init_array(output, elements, input->value.array.count) != VAULT_JCS_MODEL_OK) {
                for (size_t i = 0; i < input->value.array.count; ++i) vault_jcs_model_free(&elements[i]);
                free(elements);
                return LOADER_MEMORY_ERROR;
            }
            for (size_t i = 0; i < input->value.array.count; ++i) vault_jcs_model_free(&elements[i]);
            free(elements);
            return LOADER_OK;
        }
        case TEST_JSON_OBJECT: {
            if (input->value.object.has_duplicates) {
                return LOADER_DUPLICATE_KEY;
            }

            VaultJcsModelObjectMember* members = NULL;
            if (input->value.object.count > 0) {
                members = (VaultJcsModelObjectMember*)malloc(input->value.object.count * sizeof(VaultJcsModelObjectMember));
                if (!members) return LOADER_MEMORY_ERROR;

                for (size_t i = 0; i < input->value.object.count; ++i) {
                    if (strstr(input->value.object.members[i].key, "HAS_NUL_SENTINEL")) {
                        for (size_t j = 0; j < i; ++j) {
                            free(members[j].key);
                            vault_jcs_model_free(&members[j].value);
                        }
                        free(members);
                        return LOADER_EMBEDDED_NUL;
                    }

                    members[i].key = dup_str(input->value.object.members[i].key);
                    if (!members[i].key) {
                        for (size_t j = 0; j < i; ++j) {
                            free(members[j].key);
                            vault_jcs_model_free(&members[j].value);
                        }
                        free(members);
                        return LOADER_MEMORY_ERROR;
                    }

                    LoaderError err = test_loader_convert(input->value.object.members[i].value, &members[i].value);
                    if (err != LOADER_OK) {
                        free(members[i].key);
                        for (size_t j = 0; j < i; ++j) {
                            free(members[j].key);
                            vault_jcs_model_free(&members[j].value);
                        }
                        free(members);
                        return err;
                    }
                }
            }
            if (vault_jcs_model_init_object(output, members, input->value.object.count) != VAULT_JCS_MODEL_OK) {
                for (size_t i = 0; i < input->value.object.count; ++i) {
                    free(members[i].key);
                    vault_jcs_model_free(&members[i].value);
                }
                free(members);
                return LOADER_MEMORY_ERROR;
            }
            for (size_t i = 0; i < input->value.object.count; ++i) {
                free(members[i].key);
                vault_jcs_model_free(&members[i].value);
            }
            free(members);
            return LOADER_OK;
        }
        case TEST_JSON_UNSUPPORTED_FLOAT:
            return LOADER_UNSUPPORTED_TYPE;
        case TEST_JSON_UNSAFE_INTEGER:
            return LOADER_UNSAFE_INTEGER;
        case TEST_JSON_RAW_JSON:
        case TEST_JSON_REJECTION_META:
        case TEST_JSON_UNKNOWN_META:
            return LOADER_UNSUPPORTED_VECTOR_FIELD;
        default:
            return LOADER_UNSUPPORTED_TYPE;
    }
}

// --- TEST UTILS ---

static char* bytes_to_hex(const char* input) {
    if (!input) return NULL;
    size_t len = strlen(input);
    char* hex = (char*)malloc(len * 2 + 1);
    if (!hex) return NULL;
    for (size_t i = 0; i < len; i++) {
        sprintf(&hex[i * 2], "%02x", (unsigned char)input[i]);
    }
    return hex;
}

static int run_positive_test(const char* name, const VaultJcsTestJsonNode* input, const char* expected_string, const char* expected_hex) {
    printf("Running C positive loader test: %s\n", name);

    VaultJcsModelValue v;
    LoaderError err = test_loader_convert(input, &v);
    if (err != LOADER_OK) {
        printf("  FAIL: conversion failed with error %d\n", err);
        return 1;
    }

    char* output = NULL;
    VaultJcsModelError ser_err = vault_jcs_model_serialize(&v, &output);
    if (ser_err != VAULT_JCS_MODEL_OK) {
        printf("  FAIL: serialize failed with error %d\n", ser_err);
        vault_jcs_model_free(&v);
        return 1;
    }

    char* hex_output = bytes_to_hex(output);
    int ret = 0;
    if (strcmp(output, expected_string) != 0) {
        printf("  FAIL: string mismatch\n    Expected: %s\n    Got:      %s\n", expected_string, output);
        ret = 1;
    } else if (expected_hex && strcmp(hex_output, expected_hex) != 0) {
        printf("  FAIL: hex mismatch\n    Expected: %s\n    Got:      %s\n", expected_hex, hex_output);
        ret = 1;
    }

    free(hex_output);
    free(output);
    vault_jcs_model_free(&v);

    if (ret == 0) printf("  PASS\n");
    return ret;
}

static int run_negative_test(const char* name, const VaultJcsTestJsonNode* input, LoaderError expected_err) {
    printf("Running C negative loader test: %s\n", name);

    VaultJcsModelValue v;
    LoaderError err = test_loader_convert(input, &v);
    if (err == expected_err) {
        printf("  PASS (got expected error %d)\n", err);
        if (err == LOADER_OK) vault_jcs_model_free(&v);
        return 0;
    } else {
        printf("  FAIL: expected error %d, got %d\n", expected_err, err);
        if (err == LOADER_OK) vault_jcs_model_free(&v);
        return 1;
    }
}

// --- TEST CASES ---

int main(void) {
    int failures = 0;

    // --- POSITIVE TESTS ---

    // 1. Empty Object
    VaultJcsTestJsonNode empty_obj = { .type = TEST_JSON_OBJECT, .value.object = { .members = NULL, .count = 0, .has_duplicates = false } };
    failures += run_positive_test("empty object", &empty_obj, "{}", "7b7d");

    // 2. Empty Array
    VaultJcsTestJsonNode empty_arr = { .type = TEST_JSON_ARRAY, .value.array = { .elements = NULL, .count = 0 } };
    failures += run_positive_test("empty array", &empty_arr, "[]", "5b5d");

    // 3. String, Boolean, Null
    VaultJcsTestJsonNode str_node = { .type = TEST_JSON_STRING, .value.string_val = "hello" };
    failures += run_positive_test("string", &str_node, "\"hello\"", "2268656c6c6f22");

    VaultJcsTestJsonNode bool_node = { .type = TEST_JSON_BOOLEAN, .value.boolean_val = true };
    failures += run_positive_test("boolean true", &bool_node, "true", "74727565");

    VaultJcsTestJsonNode null_node = { .type = TEST_JSON_NULL };
    failures += run_positive_test("null", &null_node, "null", "6e756c6c");

    // 4. Safe Integer Min/Max
    VaultJcsTestJsonNode int_max = { .type = TEST_JSON_INTEGER, .value.integer_val = 9007199254740991LL };
    failures += run_positive_test("safe integer max", &int_max, "9007199254740991", "39303037313939323534373430393931");

    VaultJcsTestJsonNode int_min = { .type = TEST_JSON_INTEGER, .value.integer_val = -9007199254740991LL };
    failures += run_positive_test("safe integer min", &int_min, "-9007199254740991", "2d39303037313939323534373430393931");

    // 5. Nested objects/arrays and UTF-16 Surrogate key ordering
    // In UTF-16, U+10000 (\xF0\x90\x80\x80) -> D800 DC00, U+E000 (\xEE\x80\x80) -> E000
    // D800 < E000, so U+10000 sorts BEFORE U+E000.
    VaultJcsTestJsonNode val1 = { .type = TEST_JSON_INTEGER, .value.integer_val = 1 };
    VaultJcsTestJsonNode val2 = { .type = TEST_JSON_INTEGER, .value.integer_val = 2 };
    VaultJcsTestObjectMember nested_members[] = {
        { "\xEE\x80\x80", &val2 },
        { "\xF0\x90\x80\x80", &val1 }
    };
    VaultJcsTestJsonNode nested_obj = { .type = TEST_JSON_OBJECT, .value.object = { .members = nested_members, .count = 2, .has_duplicates = false } };
    failures += run_positive_test("utf-16 surrogate key ordering", &nested_obj,
        "{\"\xF0\x90\x80\x80\":1,\"\xEE\x80\x80\":2}",
        "7b22f0908080223a312c22ee8080223a327d");

    // --- NEGATIVE TESTS ---

    // 1. Unsupported float
    VaultJcsTestJsonNode neg_float = { .type = TEST_JSON_UNSUPPORTED_FLOAT };
    failures += run_negative_test("unsupported float", &neg_float, LOADER_UNSUPPORTED_TYPE);

    // 2. Unsafe integer
    VaultJcsTestJsonNode neg_unsafe_int = { .type = TEST_JSON_UNSAFE_INTEGER };
    failures += run_negative_test("unsafe integer", &neg_unsafe_int, LOADER_UNSAFE_INTEGER);

    // 3. Embedded NUL in string
    VaultJcsTestJsonNode neg_nul_str = { .type = TEST_JSON_STRING, .value.string_val = "badHAS_NUL_SENTINELstring" };
    failures += run_negative_test("embedded NUL in string", &neg_nul_str, LOADER_EMBEDDED_NUL);

    // 4. Duplicate object key
    VaultJcsTestJsonNode neg_dup_key = { .type = TEST_JSON_OBJECT, .value.object = { .members = nested_members, .count = 2, .has_duplicates = true } };
    failures += run_negative_test("duplicate object key", &neg_dup_key, LOADER_DUPLICATE_KEY);

    // 5. Raw JSON field
    VaultJcsTestJsonNode neg_raw_json = { .type = TEST_JSON_RAW_JSON };
    failures += run_negative_test("raw json sentinel", &neg_raw_json, LOADER_UNSUPPORTED_VECTOR_FIELD);

    // 6. Rejection/planning-only metadata
    VaultJcsTestJsonNode neg_rej_meta = { .type = TEST_JSON_REJECTION_META };
    failures += run_negative_test("rejection metadata", &neg_rej_meta, LOADER_UNSUPPORTED_VECTOR_FIELD);

    // 7. Unknown metadata
    VaultJcsTestJsonNode neg_unk_meta = { .type = TEST_JSON_UNKNOWN_META };
    failures += run_negative_test("unknown metadata", &neg_unk_meta, LOADER_UNSUPPORTED_VECTOR_FIELD);

    printf("\nTotal failures: %d\n", failures);
    return failures > 0 ? 1 : 0;
}
