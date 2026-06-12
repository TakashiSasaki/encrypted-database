#ifndef VAULT_JCS_MODEL_H
#define VAULT_JCS_MODEL_H

#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum VaultJcsModelType {
    VAULT_JCS_MODEL_TYPE_NULL,
    VAULT_JCS_MODEL_TYPE_BOOLEAN,
    VAULT_JCS_MODEL_TYPE_INTEGER,
    VAULT_JCS_MODEL_TYPE_STRING
} VaultJcsModelType;

typedef enum VaultJcsModelError {
    VAULT_JCS_MODEL_OK = 0,
    VAULT_JCS_MODEL_ERROR_MEMORY,
    VAULT_JCS_MODEL_ERROR_INVALID_ARG,
    VAULT_JCS_MODEL_ERROR_UNSAFE_INTEGER
} VaultJcsModelError;

typedef struct VaultJcsModelValue {
    VaultJcsModelType type;
    union {
        bool boolean_value;
        int64_t integer_value;
        char* string_value;
    } value;
} VaultJcsModelValue;

VaultJcsModelError vault_jcs_model_init_null(VaultJcsModelValue* value);
VaultJcsModelError vault_jcs_model_init_boolean(VaultJcsModelValue* value, bool boolean_value);
VaultJcsModelError vault_jcs_model_init_integer(VaultJcsModelValue* value, int64_t integer_value);
VaultJcsModelError vault_jcs_model_init_string(VaultJcsModelValue* value, const char* string_value);
void vault_jcs_model_free(VaultJcsModelValue* value);

#ifdef __cplusplus
}
#endif

#endif /* VAULT_JCS_MODEL_H */
