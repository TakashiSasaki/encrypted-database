#include "vault_jcs_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "generated_jcs_vectors.h"

// Simple local hex encoder for tests
static char* hex_encode(const char* data, size_t len) {
    char* hex = (char*)malloc(len * 2 + 1);
    if (!hex) return NULL;
    for (size_t i = 0; i < len; i++) {
        sprintf(hex + (i * 2), "%02x", (unsigned char)data[i]);
    }
    hex[len * 2] = '\0';
    return hex;
}

static int run_vector_test(const JcsTestVector* vector) {
    printf("Running JCS vector test: %s\n", vector->name);

    char* serialized = vault_jcs_serialize_generated_value(vector->input);
    if (!serialized) {
        printf("  FAIL: serialization returned NULL\n");
        return 1;
    }

    if (strcmp(serialized, vector->expected_string) != 0) {
        printf("  FAIL: string mismatch\n");
        printf("    Expected: %s\n", vector->expected_string);
        printf("    Got     : %s\n", serialized);
        free(serialized);
        return 1;
    }

    char* hex = hex_encode(serialized, strlen(serialized));
    if (!hex) {
        printf("  FAIL: hex encoding failed\n");
        free(serialized);
        return 1;
    }

    if (strcmp(hex, vector->expected_hex) != 0) {
        printf("  FAIL: hex mismatch\n");
        printf("    Expected: %s\n", vector->expected_hex);
        printf("    Got     : %s\n", hex);
        free(serialized);
        free(hex);
        return 1;
    }

    free(serialized);
    free(hex);
    printf("  PASS\n");
    return 0;
}

// Local regression for boolean/null
static int run_local_regression_test(void) {
    printf("Running local regression test for boolean/null...\n");

    // Create a local AST: {"b":false,"n":null,"t":true}
    static const VaultJcsValue node_false = { VAULT_JCS_BOOLEAN, { .boolean_val = false } };
    static const VaultJcsValue node_null = { VAULT_JCS_NULL, {0} };
    static const VaultJcsValue node_true = { VAULT_JCS_BOOLEAN, { .boolean_val = true } };

    // Deliberately unsorted keys to test sorting
    static const VaultJcsObjectMember members[] = {
        { "t", &node_true },
        { "b", &node_false },
        { "n", &node_null }
    };
    static const VaultJcsValue root = { VAULT_JCS_OBJECT, { .object = { members, 3 } } };

    const char* expected = "{\"b\":false,\"n\":null,\"t\":true}";
    char* serialized = vault_jcs_serialize_generated_value(&root);

    if (!serialized || strcmp(serialized, expected) != 0) {
        printf("  FAIL: boolean/null local regression mismatch\n");
        if (serialized) {
            printf("    Expected: %s\n", expected);
            printf("    Got     : %s\n", serialized);
            free(serialized);
        }
        return 1;
    }

    free(serialized);
    printf("  PASS\n");
    return 0;
}

int main(void) {
    int failures = 0;

    for (int i = 0; i < NUM_JCS_TEST_VECTORS; i++) {
        failures += run_vector_test(&JCS_TEST_VECTORS[i]);
    }

    failures += run_local_regression_test();

    if (failures > 0) {
        printf("%d tests failed.\n", failures);
        return 1;
    }

    printf("All JCS tests passed.\n");
    return 0;
}
