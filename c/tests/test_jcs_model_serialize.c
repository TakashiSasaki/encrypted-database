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

int main() {
    test_serialize_null();
    test_serialize_boolean();
    test_serialize_integer();
    test_serialize_string();
    test_serialize_array();
    test_serialize_object();
    test_serialize_nested();
    test_invalid_arguments();

    printf("C JCS model serializer tests passed.\n");
    return 0;
}
