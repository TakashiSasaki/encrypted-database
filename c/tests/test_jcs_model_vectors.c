#include "vault_jcs_model.h"
#include "vault_jcs_internal.h"
#include "generated_jcs_vectors.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// Forward declaration
static VaultJcsModelError convert_generated_to_model(const VaultJcsValue* input, VaultJcsModelValue* output);

static VaultJcsModelError convert_generated_to_model(const VaultJcsValue* input, VaultJcsModelValue* output) {
    if (!input || !output) return VAULT_JCS_MODEL_ERROR_INVALID_ARG;

    switch (input->type) {
        case VAULT_JCS_NULL:
            return vault_jcs_model_init_null(output);
        case VAULT_JCS_BOOLEAN:
            return vault_jcs_model_init_boolean(output, input->value.boolean_val);
        case VAULT_JCS_INTEGER:
            return vault_jcs_model_init_integer(output, input->value.integer_val);
        case VAULT_JCS_STRING:
            return vault_jcs_model_init_string(output, input->value.string_val);
        case VAULT_JCS_ARRAY: {
            VaultJcsModelValue* elements = NULL;
            if (input->value.array.count > 0) {
                elements = (VaultJcsModelValue*)malloc(input->value.array.count * sizeof(VaultJcsModelValue));
                if (!elements) return VAULT_JCS_MODEL_ERROR_MEMORY;

                for (size_t i = 0; i < input->value.array.count; ++i) {
                    VaultJcsModelError err = convert_generated_to_model(input->value.array.elements[i], &elements[i]);
                    if (err != VAULT_JCS_MODEL_OK) {
                        for (size_t j = 0; j < i; ++j) {
                            vault_jcs_model_free(&elements[j]);
                        }
                        free(elements);
                        return err;
                    }
                }
            }
            VaultJcsModelError err = vault_jcs_model_init_array(output, elements, input->value.array.count);
            for (size_t i = 0; i < input->value.array.count; ++i) {
                vault_jcs_model_free(&elements[i]);
            }
            free(elements);
            return err;
        }
        case VAULT_JCS_OBJECT: {
            VaultJcsModelObjectMember* members = NULL;
            if (input->value.object.count > 0) {
                members = (VaultJcsModelObjectMember*)malloc(input->value.object.count * sizeof(VaultJcsModelObjectMember));
                if (!members) return VAULT_JCS_MODEL_ERROR_MEMORY;

                for (size_t i = 0; i < input->value.object.count; ++i) {
                    members[i].key = strdup(input->value.object.members[i].key);
                    if (!members[i].key) {
                        for (size_t j = 0; j < i; ++j) {
                            free(members[j].key);
                            vault_jcs_model_free(&members[j].value);
                        }
                        free(members);
                        return VAULT_JCS_MODEL_ERROR_MEMORY;
                    }
                    VaultJcsModelError err = convert_generated_to_model(input->value.object.members[i].value, &members[i].value);
                    if (err != VAULT_JCS_MODEL_OK) {
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
            VaultJcsModelError err = vault_jcs_model_init_object(output, members, input->value.object.count);
            for (size_t i = 0; i < input->value.object.count; ++i) {
                free(members[i].key);
                vault_jcs_model_free(&members[i].value);
            }
            free(members);
            return err;
        }
        default:
            return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }
}

static int run_vector_test(const JcsTestVector* vector) {
    printf("Running vault_jcs_model vector test: %s\n", vector->name);

    VaultJcsModelValue v;
    VaultJcsModelError err = convert_generated_to_model(vector->input, &v);
    if (err != VAULT_JCS_MODEL_OK) {
        printf("  FAIL: conversion failed with error %d\n", err);
        return 1;
    }

    char* output = NULL;
    err = vault_jcs_model_serialize(&v, &output);

    if (err != VAULT_JCS_MODEL_OK) {
        printf("  FAIL: serialize failed with error %d\n", err);
        vault_jcs_model_free(&v);
        return 1;
    }

    if (strcmp(output, vector->expected_string) != 0) {
        printf("  FAIL: string mismatch\n");
        printf("    Expected: %s\n", vector->expected_string);
        printf("    Got:      %s\n", output);
        free(output);
        vault_jcs_model_free(&v);
        return 1;
    }

    free(output);
    vault_jcs_model_free(&v);
    printf("  PASS\n");
    return 0;
}

int main(void) {
    printf("Running vault_jcs_model_vectors tests from shared generated vectors...\n");
    int failures = 0;

    for (int i = 0; i < NUM_JCS_TEST_VECTORS; i++) {
        failures += run_vector_test(&JCS_TEST_VECTORS[i]);
    }

    if (failures == 0) {
        printf("All vault_jcs_model_vectors tests passed.\n");
        return 0;
    } else {
        printf("%d vault_jcs_model_vectors tests failed.\n", failures);
        return 1;
    }
}
