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

    printf("Running AAD escaping regression tests...\n");

    struct {
        const char* name;
        const char* obj_uuid;
        const char* sch_uuid;
        const char* ctype;
        const char* kid;
        const char* alg;
        const char* expected_str;
        const char* expected_hex;
    } regression_cases[] = {
        {
            "double-quote",
            "u1", "s1", "application/example; note=\"x\"", "k1", "A256GCM",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"application/example; note=\\\"x\\\"\",\"kid\":\"k1\",\"object_uuid\":\"u1\",\"schema_uuid\":\"s1\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a226170706c69636174696f6e2f6578616d706c653b206e6f74653d5c22785c22222c226b6964223a226b31222c226f626a6563745f75756964223a227531222c22736368656d615f75756964223a227331222c2276223a317d"
        },
        {
            "backslash",
            "u1", "s1", "domain\\user", "k1", "A256GCM",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"domain\\\\user\",\"kid\":\"k1\",\"object_uuid\":\"u1\",\"schema_uuid\":\"s1\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a22646f6d61696e5c5c75736572222c226b6964223a226b31222c226f626a6563745f75756964223a227531222c22736368656d615f75756964223a227331222c2276223a317d"
        },
        {
            "newline-tab",
            "u1\n", "s1\t", "type", "k1", "A256GCM",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"type\",\"kid\":\"k1\",\"object_uuid\":\"u1\\n\",\"schema_uuid\":\"s1\\t\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a2274797065222c226b6964223a226b31222c226f626a6563745f75756964223a2275315c6e222c22736368656d615f75756964223a2273315c74222c2276223a317d"
        },
        {
            "control-char-01",
            "u1", "s1", "t\x01y", "k1", "A256GCM",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"t\\u0001y\",\"kid\":\"k1\",\"object_uuid\":\"u1\",\"schema_uuid\":\"s1\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a22745c753030303179222c226b6964223a226b31222c226f626a6563745f75756964223a227531222c22736368656d615f75756964223a227331222c2276223a317d"
        }
    };

    for (size_t i = 0; i < sizeof(regression_cases) / sizeof(regression_cases[0]); ++i) {
        char* actual_string = vault_aad_record_payload_v1(
            regression_cases[i].obj_uuid, regression_cases[i].sch_uuid,
            regression_cases[i].ctype, regression_cases[i].kid, regression_cases[i].alg);

        if (!actual_string) {
            printf("FAIL: AAD helper returned NULL for regression '%s'\n", regression_cases[i].name);
            failures++;
            continue;
        }

        if (strcmp(actual_string, regression_cases[i].expected_str) != 0) {
            printf("FAIL: String mismatch for regression '%s'\n", regression_cases[i].name);
            printf("  Expected: %s\n", regression_cases[i].expected_str);
            printf("  Actual  : %s\n", actual_string);
            failures++;
            free(actual_string);
            continue;
        }

        size_t len = strlen(actual_string);
        char* actual_hex = (char*)malloc(len * 2 + 1);
        to_hex(actual_string, actual_hex);

        if (strcmp(actual_hex, regression_cases[i].expected_hex) != 0) {
            printf("FAIL: Hex mismatch for regression '%s'\n", regression_cases[i].name);
            printf("  Expected: %s\n", regression_cases[i].expected_hex);
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
