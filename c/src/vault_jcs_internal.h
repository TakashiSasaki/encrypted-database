#ifndef VAULT_JCS_INTERNAL_H
#define VAULT_JCS_INTERNAL_H

#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

// Forward declaration of the generated JCS value type
struct VaultJcsValue;

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
