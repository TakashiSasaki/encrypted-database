#include "vault_jcs_model.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define VAULT_JCS_SAFE_INTEGER_MIN (-9007199254740991LL)
#define VAULT_JCS_SAFE_INTEGER_MAX (9007199254740991LL)

void test_null_construction() {
    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_null(&v);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_NULL);
    vault_jcs_model_free(&v);
    assert(v.type == VAULT_JCS_MODEL_TYPE_NULL);
}

void test_boolean_construction() {
    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_boolean(&v, true);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_BOOLEAN);
    assert(v.value.boolean_value == true);
    vault_jcs_model_free(&v);

    err = vault_jcs_model_init_boolean(&v, false);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_BOOLEAN);
    assert(v.value.boolean_value == false);
    vault_jcs_model_free(&v);
}

void test_integer_construction() {
    VaultJcsModelValue v;
    VaultJcsModelError err;

    // Test zero
    err = vault_jcs_model_init_integer(&v, 0);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_INTEGER);
    assert(v.value.integer_value == 0);
    vault_jcs_model_free(&v);

    // Test max safe
    err = vault_jcs_model_init_integer(&v, VAULT_JCS_SAFE_INTEGER_MAX);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.value.integer_value == VAULT_JCS_SAFE_INTEGER_MAX);
    vault_jcs_model_free(&v);

    // Test min safe
    err = vault_jcs_model_init_integer(&v, VAULT_JCS_SAFE_INTEGER_MIN);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.value.integer_value == VAULT_JCS_SAFE_INTEGER_MIN);
    vault_jcs_model_free(&v);

    // Test unsafe rejection max+1
    err = vault_jcs_model_init_integer(&v, VAULT_JCS_SAFE_INTEGER_MAX + 1);
    assert(err == VAULT_JCS_MODEL_ERROR_UNSAFE_INTEGER);

    // Test unsafe rejection min-1
    err = vault_jcs_model_init_integer(&v, VAULT_JCS_SAFE_INTEGER_MIN - 1);
    assert(err == VAULT_JCS_MODEL_ERROR_UNSAFE_INTEGER);
}

void test_string_construction() {
    VaultJcsModelValue v;
    VaultJcsModelError err;

    // Test valid string
    const char* str_val = "hello world";
    err = vault_jcs_model_init_string(&v, str_val);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_STRING);
    assert(v.value.string_value != str_val); // Ensure memory is copied
    assert(strcmp(v.value.string_value, str_val) == 0);
    vault_jcs_model_free(&v);

    // Ensure properly cleaned up
    assert(v.type == VAULT_JCS_MODEL_TYPE_NULL);
    assert(v.value.string_value == NULL);

    // Test NULL string rejection
    err = vault_jcs_model_init_string(&v, NULL);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);
}

void test_array_construction() {
    VaultJcsModelValue v;
    VaultJcsModelError err;

    // Test empty array
    err = vault_jcs_model_init_array(&v, NULL, 0);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_ARRAY);
    assert(v.value.array_value.count == 0);
    assert(v.value.array_value.elements == NULL);
    vault_jcs_model_free(&v);

    // Test array with elements
    VaultJcsModelValue elements[3];
    vault_jcs_model_init_null(&elements[0]);
    vault_jcs_model_init_boolean(&elements[1], true);
    vault_jcs_model_init_integer(&elements[2], 42);

    err = vault_jcs_model_init_array(&v, elements, 3);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_ARRAY);
    assert(v.value.array_value.count == 3);
    assert(v.value.array_value.elements != NULL);

    // Verify deep copy
    assert(v.value.array_value.elements[0].type == VAULT_JCS_MODEL_TYPE_NULL);
    assert(v.value.array_value.elements[1].type == VAULT_JCS_MODEL_TYPE_BOOLEAN);
    assert(v.value.array_value.elements[1].value.boolean_value == true);
    assert(v.value.array_value.elements[2].type == VAULT_JCS_MODEL_TYPE_INTEGER);
    assert(v.value.array_value.elements[2].value.integer_value == 42);

    // Modifying originals shouldn't affect copy
    elements[1].value.boolean_value = false;
    assert(v.value.array_value.elements[1].value.boolean_value == true);

    vault_jcs_model_free(&v);
    vault_jcs_model_free(&elements[0]);
    vault_jcs_model_free(&elements[1]);
    vault_jcs_model_free(&elements[2]);
}

void test_object_construction() {
    VaultJcsModelValue v;
    VaultJcsModelError err;

    // Test empty object
    err = vault_jcs_model_init_object(&v, NULL, 0);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_OBJECT);
    assert(v.value.object_value.count == 0);
    assert(v.value.object_value.members == NULL);
    vault_jcs_model_free(&v);

    // Test object with elements
    VaultJcsModelObjectMember members[2];
    members[0].key = "key1";
    vault_jcs_model_init_string(&members[0].value, "value1");
    members[1].key = "key2";
    vault_jcs_model_init_integer(&members[1].value, 123);

    err = vault_jcs_model_init_object(&v, members, 2);
    assert(err == VAULT_JCS_MODEL_OK);
    assert(v.type == VAULT_JCS_MODEL_TYPE_OBJECT);
    assert(v.value.object_value.count == 2);
    assert(v.value.object_value.members != NULL);

    // Verify deep copy
    assert(strcmp(v.value.object_value.members[0].key, "key1") == 0);
    assert(v.value.object_value.members[0].key != members[0].key);
    assert(v.value.object_value.members[0].value.type == VAULT_JCS_MODEL_TYPE_STRING);
    assert(strcmp(v.value.object_value.members[0].value.value.string_value, "value1") == 0);

    assert(strcmp(v.value.object_value.members[1].key, "key2") == 0);
    assert(v.value.object_value.members[1].value.type == VAULT_JCS_MODEL_TYPE_INTEGER);
    assert(v.value.object_value.members[1].value.value.integer_value == 123);

    vault_jcs_model_free(&v);
    vault_jcs_model_free(&members[0].value);
    vault_jcs_model_free(&members[1].value);

    // Test duplicate key rejection
    VaultJcsModelObjectMember duplicate_members[2];
    duplicate_members[0].key = "same";
    vault_jcs_model_init_null(&duplicate_members[0].value);
    duplicate_members[1].key = "same";
    vault_jcs_model_init_null(&duplicate_members[1].value);

    err = vault_jcs_model_init_object(&v, duplicate_members, 2);
    assert(err == VAULT_JCS_MODEL_ERROR_DUPLICATE_KEY);

    vault_jcs_model_free(&duplicate_members[0].value);
    vault_jcs_model_free(&duplicate_members[1].value);

    // Test NULL key rejection
    VaultJcsModelObjectMember null_key_members[1];
    null_key_members[0].key = NULL;
    vault_jcs_model_init_null(&null_key_members[0].value);

    err = vault_jcs_model_init_object(&v, null_key_members, 1);
    assert(err == VAULT_JCS_MODEL_ERROR_INVALID_ARG);

    vault_jcs_model_free(&null_key_members[0].value);
}

void test_utf16_surrogate_ordering() {
    // U+10000 = F0 90 80 80 (UTF-8) -> D800 DC00 (UTF-16)
    // U+E000  = EE 80 80 (UTF-8)    -> E000 (UTF-16)
    // UTF-16 Order: D800 DC00 before E000 (U+10000 before U+E000)
    const char* key1 = "\xf0\x90\x80\x80"; // U+10000
    const char* key2 = "\xee\x80\x80";     // U+E000

    VaultJcsModelObjectMember members[2];
    members[0].key = (char*)key2;
    vault_jcs_model_init_integer(&members[0].value, 2);
    members[1].key = (char*)key1;
    vault_jcs_model_init_integer(&members[1].value, 1);

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 2);
    assert(err == VAULT_JCS_MODEL_OK);

    char* out = NULL;
    err = vault_jcs_model_serialize(&v, &out);
    assert(err == VAULT_JCS_MODEL_OK);

    // Expected serialization: {"\xf0\x90\x80\x80":1,"\xee\x80\x80":2}
    const char* expected = "{\"\xf0\x90\x80\x80\":1,\"\xee\x80\x80\":2}";
    assert(strcmp(out, expected) == 0);

    free(out);
    vault_jcs_model_free(&v);
}

void test_nested_composite() {
    VaultJcsModelValue v;
    VaultJcsModelError err;

    VaultJcsModelValue array_elems[1];
    vault_jcs_model_init_string(&array_elems[0], "nested_string");

    VaultJcsModelObjectMember members[1];
    members[0].key = "nested_array";
    vault_jcs_model_init_array(&members[0].value, array_elems, 1);

    err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);

    // Cleanup originals
    vault_jcs_model_free(&array_elems[0]);
    vault_jcs_model_free(&members[0].value);

    // Verify copy
    assert(v.type == VAULT_JCS_MODEL_TYPE_OBJECT);
    assert(v.value.object_value.count == 1);
    assert(v.value.object_value.members[0].value.type == VAULT_JCS_MODEL_TYPE_ARRAY);
    assert(v.value.object_value.members[0].value.value.array_value.count == 1);
    assert(v.value.object_value.members[0].value.value.array_value.elements[0].type == VAULT_JCS_MODEL_TYPE_STRING);
    assert(strcmp(v.value.object_value.members[0].value.value.array_value.elements[0].value.string_value, "nested_string") == 0);

    vault_jcs_model_free(&v);
}

int main() {
    printf("Running C JCS internal model tests...\n");
    test_null_construction();
    test_boolean_construction();
    test_integer_construction();
    test_string_construction();
    test_array_construction();
    test_object_construction();
    test_utf16_surrogate_ordering();
    test_nested_composite();
    printf("C JCS internal model tests passed.\n");
    return 0;
}
