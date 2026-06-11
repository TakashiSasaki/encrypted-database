#ifndef VAULT_JCS_INTERNAL_H
#define VAULT_JCS_INTERNAL_H

#include <stddef.h>
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief JCS Test Fixture Contract
 *
 * This section defines the generated-AST test fixture ABI/layout for JCS basic vectors.
 * C and C++ share this generated-AST fixture layout as an internal test-harness contract;
 * serialization remains independently implemented in each language.
 */

typedef enum {
    VAULT_JCS_NULL,
    VAULT_JCS_BOOLEAN,
    VAULT_JCS_INTEGER,
    VAULT_JCS_STRING,
    VAULT_JCS_ARRAY,
    VAULT_JCS_OBJECT
} VaultJcsType;

typedef struct VaultJcsValue VaultJcsValue;

typedef struct {
    const char* key;
    const VaultJcsValue* value;
} VaultJcsObjectMember;

struct VaultJcsValue {
    VaultJcsType type;
    union {
        bool boolean_val;
        int64_t integer_val;
        const char* string_val;
        struct {
            const VaultJcsValue* const* elements;
            size_t count;
        } array;
        struct {
            const VaultJcsObjectMember* members;
            size_t count;
        } object;
    } value;
};

typedef struct {
    const char* name;
    const char* description;
    const VaultJcsValue* input;
    const char* expected_string;
    const char* expected_hex;
} JcsTestVector;


/**
 * @brief Internal JCS serializer scaffold.
 *
 * Serializes the generated VaultJcsValue AST to a dynamically allocated
 * NUL-terminated JCS string.
 *
 * Supported features:
 * - string escaping
 * - lexicographic object key sorting
 * - booleans, null, strings, integers, arrays, objects
 *
 * @param value The root AST node.
 * @return A newly allocated string, or NULL on error. Caller must free() it.
 */
char* vault_jcs_serialize_generated_value(const struct VaultJcsValue* value);

#ifdef __cplusplus
}
#endif

#endif /* VAULT_JCS_INTERNAL_H */
