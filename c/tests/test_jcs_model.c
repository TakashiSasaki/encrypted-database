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

int main() {
    printf("Running C JCS internal model tests...\n");
    test_null_construction();
    test_boolean_construction();
    test_integer_construction();
    test_string_construction();
    printf("C JCS internal model tests passed.\n");
    return 0;
}
