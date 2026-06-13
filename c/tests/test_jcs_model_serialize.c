#include "vault_jcs_model.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define VAULT_JCS_SAFE_INTEGER_MIN (-9007199254740991LL)
#define VAULT_JCS_SAFE_INTEGER_MAX (9007199254740991LL)

void test_serialize_null() {
    VaultJcsModelValue v;
    vault_jcs_model_init_null(&v);

    char* output = NULL;
    VaultJcsModelError err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "null") == 0);

    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_boolean() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    vault_jcs_model_init_boolean(&v, true);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "true") == 0);
    free(output);
    vault_jcs_model_free(&v);

    vault_jcs_model_init_boolean(&v, false);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "false") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_integer() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    vault_jcs_model_init_integer(&v, 0);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "0") == 0);
    free(output);
    vault_jcs_model_free(&v);

    vault_jcs_model_init_integer(&v, VAULT_JCS_SAFE_INTEGER_MIN);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "-9007199254740991") == 0);
    free(output);
    vault_jcs_model_free(&v);

    vault_jcs_model_init_integer(&v, VAULT_JCS_SAFE_INTEGER_MAX);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "9007199254740991") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_string() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // Normal string
    vault_jcs_model_init_string(&v, "hello world");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "\"hello world\"") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Escaped characters
    vault_jcs_model_init_string(&v, "line1\nline2\t\"quoted\"\\back");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "\"line1\\nline2\\t\\\"quoted\\\"\\\\back\"") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Control characters < 0x20
    vault_jcs_model_init_string(&v, "hello\x01\x1F");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "\"hello\\u0001\\u001f\"") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_array() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // Empty array
    vault_jcs_model_init_array(&v, NULL, 0);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "[]") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Mixed array
    VaultJcsModelValue elements[3];
    vault_jcs_model_init_null(&elements[0]);
    vault_jcs_model_init_boolean(&elements[1], true);
    vault_jcs_model_init_integer(&elements[2], 42);

    vault_jcs_model_init_array(&v, elements, 3);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "[null,true,42]") == 0);
    free(output);
    vault_jcs_model_free(&v);

    vault_jcs_model_free(&elements[0]);
    vault_jcs_model_free(&elements[1]);
    vault_jcs_model_free(&elements[2]);
}

void test_serialize_object() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // Empty object
    vault_jcs_model_init_object(&v, NULL, 0);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "{}") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Object with unsorted ASCII keys to confirm strcmp sort
    VaultJcsModelObjectMember members[3];
    members[0].key = "z";
    vault_jcs_model_init_integer(&members[0].value, 3);
    members[1].key = "a";
    vault_jcs_model_init_integer(&members[1].value, 1);
    members[2].key = "m";
    vault_jcs_model_init_integer(&members[2].value, 2);

    vault_jcs_model_init_object(&v, members, 3);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "{\"a\":1,\"m\":2,\"z\":3}") == 0);
    free(output);
    vault_jcs_model_free(&v);

    vault_jcs_model_free(&members[0].value);
    vault_jcs_model_free(&members[1].value);
    vault_jcs_model_free(&members[2].value);
}

void test_serialize_object_ordering_utf16() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // BMP non-ASCII: "あ" (U+3042), "い" (U+3044)
    VaultJcsModelObjectMember members_bmp[2];
    members_bmp[0].key = "\xE3\x81\x84"; // "い"
    vault_jcs_model_init_integer(&members_bmp[0].value, 2);
    members_bmp[1].key = "\xE3\x81\x82"; // "あ"
    vault_jcs_model_init_integer(&members_bmp[1].value, 1);

    err = vault_jcs_model_init_object(&v, members_bmp, 2);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    // "あ" (0x3042) < "い" (0x3044)
    assert(strcmp(output, "{\"\\u3042\":1,\"\\u3044\":2}") == 0 || strcmp(output, "{\"\xE3\x81\x82\":1,\"\xE3\x81\x84\":2}") == 0);
    // We check exact output, model outputs original strings (no re-escaping for non-control characters in this simple model, so it outputs UTF-8)
    assert(strcmp(output, "{\"\xE3\x81\x82\":1,\"\xE3\x81\x84\":2}") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Surrogate-pair sensitive: U+2603 SNOWMAN vs U+1F600 GRINNING FACE
    VaultJcsModelObjectMember members_surrogate[2];
    members_surrogate[0].key = "\xF0\x9F\x98\x80"; // U+1F600 (Surrogates: D83D DE00)
    vault_jcs_model_init_integer(&members_surrogate[0].value, 2);
    members_surrogate[1].key = "\xE2\x98\x83";     // U+2603 (Code unit: 2603)
    vault_jcs_model_init_integer(&members_surrogate[1].value, 1);

    err = vault_jcs_model_init_object(&v, members_surrogate, 2);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    // 0x2603 < 0xD83D
    assert(strcmp(output, "{\"\xE2\x98\x83\":1,\"\xF0\x9F\x98\x80\":2}") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Mixed ASCII / non-ASCII
    VaultJcsModelObjectMember members_mixed[3];
    members_mixed[0].key = "\xE2\x98\x83"; // U+2603
    vault_jcs_model_init_integer(&members_mixed[0].value, 3);
    members_mixed[1].key = "a";            // U+0061
    vault_jcs_model_init_integer(&members_mixed[1].value, 1);
    members_mixed[2].key = "\xC2\xA2";     // U+00A2 CENT SIGN
    vault_jcs_model_init_integer(&members_mixed[2].value, 2);

    err = vault_jcs_model_init_object(&v, members_mixed, 3);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    // 0x0061 < 0x00A2 < 0x2603
    assert(strcmp(output, "{\"a\":1,\"\xC2\xA2\":2,\"\xE2\x98\x83\":3}") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // No Unicode Normalization: Precomposed vs Decomposed
    VaultJcsModelObjectMember members_norm[2];
    members_norm[0].key = "\xC3\xA9";       // U+00E9 (Precomposed é)
    vault_jcs_model_init_integer(&members_norm[0].value, 2);
    members_norm[1].key = "e\xCC\x81";      // U+0065 U+0301 (Decomposed é)
    vault_jcs_model_init_integer(&members_norm[1].value, 1);

    err = vault_jcs_model_init_object(&v, members_norm, 2);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    // U+0065 < U+00E9
    assert(strcmp(output, "{\"e\xCC\x81\":1,\"\xC3\xA9\":2}") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_invalid_utf8() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // 1. Invalid leading byte
    VaultJcsModelObjectMember members[1];
    members[0].key = "hello\xFFworld"; // Invalid byte \xFF
    vault_jcs_model_init_integer(&members[0].value, 1);
    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL);
    vault_jcs_model_free(&v);

    // 2. Overlong encoding
    members[0].key = "\xC0\xAF";
    vault_jcs_model_init_integer(&members[0].value, 1);
    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL);
    vault_jcs_model_free(&v);

    // 3. Truncated multi-byte sequence
    members[0].key = "\xE2\x98";
    vault_jcs_model_init_integer(&members[0].value, 1);
    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL);
    vault_jcs_model_free(&v);

    // 4. UTF-8 encoding of surrogate U+D800
    members[0].key = "\xED\xA0\x80";
    vault_jcs_model_init_integer(&members[0].value, 1);
    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL);
    vault_jcs_model_free(&v);

    // 5. Above U+10FFFF
    members[0].key = "\xF4\x90\x80\x80"; // U+110000
    vault_jcs_model_init_integer(&members[0].value, 1);
    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL);
    vault_jcs_model_free(&v);
}


void test_serialize_nested() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    VaultJcsModelValue arr_elements[2];
    vault_jcs_model_init_string(&arr_elements[0], "value");
    vault_jcs_model_init_null(&arr_elements[1]);
    VaultJcsModelValue inner_array;
    vault_jcs_model_init_array(&inner_array, arr_elements, 2);

    VaultJcsModelObjectMember members[1];
    members[0].key = "key";
    members[0].value = inner_array;

    vault_jcs_model_init_object(&v, members, 1);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);
    assert(strcmp(output, "{\"key\":[\"value\",null]}") == 0);

    free(output);
    vault_jcs_model_free(&v);
    vault_jcs_model_free(&arr_elements[0]);
    vault_jcs_model_free(&arr_elements[1]);
    // Note: v took deep copy of inner_array (and thus arr_elements)
    // we must also free inner_array and arr_elements
    vault_jcs_model_free(&inner_array);
}

void test_invalid_arguments() {
    VaultJcsModelValue v;
    vault_jcs_model_init_null(&v);
    VaultJcsModelError err;

    // NULL output pointer
    err = vault_jcs_model_serialize(&v, NULL);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);

    // NULL value pointer
    char* output = (char*)0x1234; // Some non-null address
    err = vault_jcs_model_serialize(NULL, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL); // Should set output to NULL on failure if output is provided

    vault_jcs_model_free(&v);
}

void test_malformed_internal_values() {
    VaultJcsModelValue v;
    char* output = (char*)0x1234;
    VaultJcsModelError err;

    // Invalid enum type
    v.type = (VaultJcsModelType)999;
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_SERIALIZE);
    assert(output == NULL);

    // String type with NULL string
    v.type = VAULT_JCS_MODEL_TYPE_STRING;
    v.value.string_value = NULL;
    output = (char*)0x1234;
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_SERIALIZE);
    assert(output == NULL);

    // Array type with count > 0 but NULL elements
    v.type = VAULT_JCS_MODEL_TYPE_ARRAY;
    v.value.array_value.count = 1;
    v.value.array_value.elements = NULL;
    output = (char*)0x1234;
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_SERIALIZE);
    assert(output == NULL);

    // Object type with count > 0 but NULL members
    v.type = VAULT_JCS_MODEL_TYPE_OBJECT;
    v.value.object_value.count = 1;
    v.value.object_value.members = NULL;
    output = (char*)0x1234;
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_SERIALIZE);
    assert(output == NULL);

    // Object member with NULL key
    VaultJcsModelObjectMember members[1];
    members[0].key = NULL;
    vault_jcs_model_init_null(&members[0].value);

    v.type = VAULT_JCS_MODEL_TYPE_OBJECT;
    v.value.object_value.count = 1;
    v.value.object_value.members = members;
    output = (char*)0x1234;
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_SERIALIZE);
    assert(output == NULL);

    vault_jcs_model_free(&members[0].value);
}

void test_serialize_buffer_growth() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    const size_t array_size = 2000;
    VaultJcsModelValue* elements = (VaultJcsModelValue*)malloc(array_size * sizeof(VaultJcsModelValue));
    assert(elements != NULL);

    for (size_t i = 0; i < array_size; i++) {
        vault_jcs_model_init_string(&elements[i], "test_growth_element");
    }

    err = vault_jcs_model_init_array(&v, elements, array_size);
    assert(err == VAULT_JCS_MODEL_OK);

    for (size_t i = 0; i < array_size; i++) {
        vault_jcs_model_free(&elements[i]);
    }
    free(elements);

    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(output != NULL);

    // Verify format
    size_t out_len = strlen(output);
    assert(out_len > 0);
    assert(output[0] == '[');
    assert(output[out_len - 1] == ']');

    // Verify content prefix
    assert(strncmp(output, "[\"test_growth_element\",", 23) == 0);

    free(output);
    vault_jcs_model_free(&v);
}


void test_serialize_control_characters() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // Test specific short escapes
    vault_jcs_model_init_string(&v, "backspace\b formfeed\f newline\n cr\r tab\t quote\" slash/");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    // Solidus '/' must NOT be escaped
    assert(strcmp(output, "\"backspace\\b formfeed\\f newline\\n cr\\r tab\\t quote\\\" slash/\"") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Test other control characters
    vault_jcs_model_init_string(&v, "ctrl\x01\x1F");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "\"ctrl\\u0001\\u001f\"") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_empty_string_and_key() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // Empty string value
    vault_jcs_model_init_string(&v, "");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "\"\"") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // Empty object key
    VaultJcsModelObjectMember members[1];
    members[0].key = "";
    vault_jcs_model_init_integer(&members[0].value, 1);
    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "{\"\":1}") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_non_bmp() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    // String value non-BMP preserving
    vault_jcs_model_init_string(&v, "😊");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "\"\xF0\x9F\x98\x8A\"") == 0);
    free(output);
    vault_jcs_model_free(&v);

    // String value non-ASCII BMP preserving
    vault_jcs_model_init_string(&v, "äöü");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "\"\xC3\xA4\xC3\xB6\xC3\xBC\"") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_deep_nesting() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    VaultJcsModelValue inner;
    vault_jcs_model_init_integer(&inner, 1);

    VaultJcsModelObjectMember m_c[1];
    m_c[0].key = "c";
    m_c[0].value = inner;
    VaultJcsModelValue val_c;
    vault_jcs_model_init_object(&val_c, m_c, 1);

    VaultJcsModelObjectMember m_b[1];
    m_b[0].key = "b";
    m_b[0].value = val_c;
    VaultJcsModelValue val_b;
    vault_jcs_model_init_object(&val_b, m_b, 1);

    VaultJcsModelObjectMember m_a[1];
    m_a[0].key = "a";
    m_a[0].value = val_b;
    VaultJcsModelValue val_a;
    vault_jcs_model_init_object(&val_a, m_a, 1);

    err = vault_jcs_model_serialize(&val_a, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "{\"a\":{\"b\":{\"c\":1}}}") == 0);

    free(output);
    vault_jcs_model_free(&val_a);
    vault_jcs_model_free(&val_b);
    vault_jcs_model_free(&val_c);
    vault_jcs_model_free(&inner);
}


void test_serialize_utf16_ordering() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    VaultJcsModelObjectMember members[4];
    members[0].key = "𐀀"; // U+10000 -> D800 DC00
    vault_jcs_model_init_integer(&members[0].value, 1);
    members[1].key = "嶲"; // U+2F9F4 -> D87E DDF4
    vault_jcs_model_init_integer(&members[1].value, 2);
    members[2].key = "a"; // U+0061
    vault_jcs_model_init_integer(&members[2].value, 3);
    members[3].key = "é"; // U+00E9
    vault_jcs_model_init_integer(&members[3].value, 4);

    err = vault_jcs_model_init_object(&v, members, 4);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "{\"a\":3,\"é\":4,\"𐀀\":1,\"嶲\":2}") == 0 || strcmp(output, "{\"a\":3,\"\xC3\xA9\":4,\"\xF0\x90\x80\x80\":1,\"\xF0\xAF\xA7\xB4\":2}") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_safe_integer_boundaries() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    vault_jcs_model_init_integer(&v, 9007199254740991LL);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "9007199254740991") == 0);
    free(output);
    vault_jcs_model_free(&v);

    vault_jcs_model_init_integer(&v, -9007199254740991LL);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "-9007199254740991") == 0);
    free(output);
    vault_jcs_model_free(&v);
}

void test_serialize_backslash_escape() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    vault_jcs_model_init_string(&v, "back\\\\slash");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(strcmp(output, "\"back\\\\\\\\slash\"") == 0);
    free(output);
    vault_jcs_model_free(&v);
}


void test_serialize_invalid_utf8_object_keys_more() {
    VaultJcsModelValue v;
    char* output = NULL;
    VaultJcsModelError err;

    VaultJcsModelObjectMember members[1];

    // Test invalid UTF-8 (e.g. \xFF)
    members[0].key = "\xFF";
    vault_jcs_model_init_integer(&members[0].value, 1);
    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL);
    vault_jcs_model_free(&v);

    // Test invalid UTF-8 for string value
    // Our C implementation may currently defer validation on string values,
    // so let's see if it successfully passes bytes through
    vault_jcs_model_init_string(&v, "\xFF");
    err = vault_jcs_model_serialize(&v, &output);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
    assert(output == NULL);
    free(output);
    vault_jcs_model_free(&v);
}

int main() {
    test_serialize_invalid_utf8_object_keys_more();
    test_serialize_utf16_ordering();
    test_serialize_safe_integer_boundaries();
    test_serialize_backslash_escape();
    test_serialize_control_characters();
    test_serialize_empty_string_and_key();
    test_serialize_non_bmp();
    test_serialize_deep_nesting();
    test_serialize_null();
    test_serialize_boolean();
    test_serialize_integer();
    test_serialize_string();
    test_serialize_array();
    test_serialize_object();
    test_serialize_object_ordering_utf16();
    test_serialize_invalid_utf8();
    test_serialize_nested();
    test_invalid_arguments();
    test_malformed_internal_values();
    test_serialize_buffer_growth();

    printf("C JCS model serializer tests passed.\n");
    return 0;
}
