#include "vault_jcs_model.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

static void assert_serialize_equals(const char* name, const VaultJcsModelValue* value, const char* expected) {
    char* output = NULL;
    VaultJcsModelError err = vault_jcs_model_serialize(value, &output);

    if (err != VAULT_JCS_MODEL_OK) {
        printf("Test '%s' failed: expected success, got error %d\n", name, err);
        assert(0);
    }

    if (strcmp(output, expected) != 0) {
        printf("Test '%s' failed:\nExpected: %s\nGot:      %s\n", name, expected, output);
        free(output);
        assert(0);
    }

    free(output);
    printf("Test '%s' passed.\n", name);
}

void test_empty_object() {
    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, NULL, 0);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("empty-object", &v, "{}");
    vault_jcs_model_free(&v);
}

void test_empty_array() {
    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_array(&v, NULL, 0);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("empty-array", &v, "[]");
    vault_jcs_model_free(&v);
}

void test_object_key_ordering() {
    VaultJcsModelObjectMember members[3];
    members[0].key = strdup("b");
    vault_jcs_model_init_integer(&members[0].value, 2);
    members[1].key = strdup("a");
    vault_jcs_model_init_integer(&members[1].value, 1);
    members[2].key = strdup("c");
    vault_jcs_model_init_integer(&members[2].value, 3);

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 3);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("object-key-ordering", &v, "{\"a\":1,\"b\":2,\"c\":3}");

    for (int i = 0; i < 3; ++i) {
        free(members[i].key);
        vault_jcs_model_free(&members[i].value);
    }
    vault_jcs_model_free(&v);
}

void test_nested_objects() {
    VaultJcsModelObjectMember inner_members[2];
    inner_members[0].key = strdup("d");
    vault_jcs_model_init_integer(&inner_members[0].value, 4);
    inner_members[1].key = strdup("e");
    vault_jcs_model_init_array(&inner_members[1].value, NULL, 0); // empty array

    VaultJcsModelValue inner_obj;
    vault_jcs_model_init_object(&inner_obj, inner_members, 2);

    VaultJcsModelObjectMember members[1];
    members[0].key = strdup("nested");
    members[0].value = inner_obj;

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("nested-objects", &v, "{\"nested\":{\"d\":4,\"e\":[]}}");

    free(inner_members[0].key);
    vault_jcs_model_free(&inner_members[0].value);
    free(inner_members[1].key);
    vault_jcs_model_free(&inner_members[1].value);
    vault_jcs_model_free(&inner_obj);

    free(members[0].key);
    vault_jcs_model_free(&v);
}

void test_strings() {
    VaultJcsModelObjectMember members[1];
    members[0].key = strdup("string");
    vault_jcs_model_init_string(&members[0].value, "hello world");

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("strings", &v, "{\"string\":\"hello world\"}");

    free(members[0].key);
    vault_jcs_model_free(&members[0].value);
    vault_jcs_model_free(&v);
}

void test_escaping() {
    VaultJcsModelObjectMember members[1];
    members[0].key = strdup("escape");
    vault_jcs_model_init_string(&members[0].value, "\"\\\b\f\n\r\t");

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("escaping", &v, "{\"escape\":\"\\\"\\\\\\b\\f\\n\\r\\t\"}");

    free(members[0].key);
    vault_jcs_model_free(&members[0].value);
    vault_jcs_model_free(&v);
}

void test_integers() {
    VaultJcsModelObjectMember members[3];
    members[0].key = strdup("int");
    vault_jcs_model_init_integer(&members[0].value, 42);
    members[1].key = strdup("zero");
    vault_jcs_model_init_integer(&members[1].value, 0);
    members[2].key = strdup("neg");
    vault_jcs_model_init_integer(&members[2].value, -100);

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 3);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("integers", &v, "{\"int\":42,\"neg\":-100,\"zero\":0}");

    for (int i = 0; i < 3; ++i) {
        free(members[i].key);
        vault_jcs_model_free(&members[i].value);
    }
    vault_jcs_model_free(&v);
}

void test_arrays() {
    VaultJcsModelValue elements[3];
    vault_jcs_model_init_integer(&elements[0], 3);
    vault_jcs_model_init_integer(&elements[1], 1);

    VaultJcsModelObjectMember members[2];
    members[0].key = strdup("b");
    vault_jcs_model_init_integer(&members[0].value, 2);
    members[1].key = strdup("a");
    vault_jcs_model_init_integer(&members[1].value, 1);

    vault_jcs_model_init_object(&elements[2], members, 2);

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_array(&v, elements, 3);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("arrays", &v, "[3,1,{\"a\":1,\"b\":2}]");

    vault_jcs_model_free(&elements[0]);
    vault_jcs_model_free(&elements[1]);
    for (int i = 0; i < 2; ++i) {
        free(members[i].key);
        vault_jcs_model_free(&members[i].value);
    }
    vault_jcs_model_free(&elements[2]);
    vault_jcs_model_free(&v);
}

void test_booleans_and_null() {
    VaultJcsModelObjectMember members[3];
    members[0].key = strdup("true_val");
    vault_jcs_model_init_boolean(&members[0].value, true);
    members[1].key = strdup("null_val");
    vault_jcs_model_init_null(&members[1].value);
    members[2].key = strdup("false_val");
    vault_jcs_model_init_boolean(&members[2].value, false);

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 3);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("booleans-and-null", &v, "{\"false_val\":false,\"null_val\":null,\"true_val\":true}");

    for (int i = 0; i < 3; ++i) {
        free(members[i].key);
        vault_jcs_model_free(&members[i].value);
    }
    vault_jcs_model_free(&v);
}

void test_safe_integer_max() {
    VaultJcsModelObjectMember members[1];
    members[0].key = strdup("max");
    vault_jcs_model_init_integer(&members[0].value, 9007199254740991LL);

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("safe-integer-max", &v, "{\"max\":9007199254740991}");

    free(members[0].key);
    vault_jcs_model_free(&members[0].value);
    vault_jcs_model_free(&v);
}

void test_safe_integer_min() {
    VaultJcsModelObjectMember members[1];
    members[0].key = strdup("min");
    vault_jcs_model_init_integer(&members[0].value, -9007199254740991LL);

    VaultJcsModelValue v;
    VaultJcsModelError err = vault_jcs_model_init_object(&v, members, 1);
    assert(err == VAULT_JCS_MODEL_OK);

    assert_serialize_equals("safe-integer-min", &v, "{\"min\":-9007199254740991}");

    free(members[0].key);
    vault_jcs_model_free(&members[0].value);
    vault_jcs_model_free(&v);
}

int main() {
    printf("Running vault_jcs_model_vectors tests...\n");
    test_empty_object();
    test_empty_array();
    test_object_key_ordering();
    test_nested_objects();
    test_strings();
    test_escaping();
    test_integers();
    test_arrays();
    test_booleans_and_null();
    test_safe_integer_max();
    test_safe_integer_min();
    printf("All vault_jcs_model_vectors tests passed.\n");
    return 0;
}
