#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "vault_aad_internal.h"
#include "generated_aad_vectors.h"

static void to_hex(const char* input, char* output) {
    size_t len = strlen(input);
    for (size_t i = 0; i < len; ++i) {
        sprintf(output + (i * 2), "%02x", (unsigned char)input[i]);
    }
    output[len * 2] = '\0';
}

int main(void) {
    int failures = 0;

    printf("Running AAD vector tests...\n");

    for (int i = 0; i < NUM_AAD_TEST_VECTORS; ++i) {
        const AadTestVector* v = &AAD_TEST_VECTORS[i];
        char* actual_string = NULL;

        if (strcmp(v->policy, "record-payload-v1") == 0) {
            actual_string = vault_aad_record_payload_v1(v->object_uuid, v->schema_uuid, v->content_type, v->kid, v->alg);
        } else if (strcmp(v->policy, "wrap-database-key-v1") == 0) {
            actual_string = vault_aad_wrap_database_key_v1(v->wrapped_kid, v->wrapping_kid);
        } else if (strcmp(v->policy, "wrap-record-key-v1") == 0) {
            actual_string = vault_aad_wrap_record_key_v1(v->wrapped_kid, v->wrapping_kid);
        } else {
            printf("FAIL: Unknown policy '%s' for vector '%s'\n", v->policy, v->name);
            failures++;
            continue;
        }

        if (!actual_string) {
            printf("FAIL: AAD helper returned NULL for vector '%s'\n", v->name);
            failures++;
            continue;
        }

        if (strcmp(actual_string, v->expected_string) != 0) {
            printf("FAIL: String mismatch for vector '%s'\n", v->name);
            printf("  Expected: %s\n", v->expected_string);
            printf("  Actual  : %s\n", actual_string);
            failures++;
            free(actual_string);
            continue;
        }

        size_t len = strlen(actual_string);
        char* actual_hex = (char*)malloc(len * 2 + 1);
        if (!actual_hex) {
            printf("FAIL: Out of memory\n");
            free(actual_string);
            failures++;
            continue;
        }

        to_hex(actual_string, actual_hex);

        if (strcmp(actual_hex, v->expected_hex) != 0) {
            printf("FAIL: Hex mismatch for vector '%s'\n", v->name);
            printf("  Expected: %s\n", v->expected_hex);
            printf("  Actual  : %s\n", actual_hex);
            failures++;
        }

        free(actual_hex);
        free(actual_string);
    }

    if (failures == 0) {
        printf("All AAD vector tests passed.\n");
        return 0;
    } else {
        printf("%d AAD vector test(s) failed.\n", failures);
        return 1;
    }
}
