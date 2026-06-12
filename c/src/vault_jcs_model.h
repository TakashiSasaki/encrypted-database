#ifndef VAULT_JCS_MODEL_H
#define VAULT_JCS_MODEL_H

#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum VaultJcsModelType {
    VAULT_JCS_MODEL_TYPE_NULL,
    VAULT_JCS_MODEL_TYPE_BOOLEAN,
    VAULT_JCS_MODEL_TYPE_INTEGER,
    VAULT_JCS_MODEL_TYPE_STRING,
    VAULT_JCS_MODEL_TYPE_ARRAY,
    VAULT_JCS_MODEL_TYPE_OBJECT
} VaultJcsModelType;

typedef enum VaultJcsModelError {
    VAULT_JCS_MODEL_OK = 0,
    VAULT_JCS_MODEL_ERROR_MEMORY,
    VAULT_JCS_MODEL_ERROR_INVALID_ARG,
    VAULT_JCS_MODEL_ERROR_UNSAFE_INTEGER,
    VAULT_JCS_MODEL_ERROR_DUPLICATE_KEY
} VaultJcsModelError;

typedef struct VaultJcsModelValue VaultJcsModelValue;

struct VaultJcsModelValue {
    VaultJcsModelType type;
    union {
        bool boolean_value;
        int64_t integer_value;
        char* string_value;
        struct {
            VaultJcsModelValue* elements;
            size_t count;
        } array_value;
        struct {
            struct VaultJcsModelObjectMember* members;
            size_t count;
        } object_value;
    } value;
};

typedef struct VaultJcsModelObjectMember {
    char* key;
    VaultJcsModelValue value;
} VaultJcsModelObjectMember;


VaultJcsModelError vault_jcs_model_init_null(VaultJcsModelValue* value);
VaultJcsModelError vault_jcs_model_init_boolean(VaultJcsModelValue* value, bool boolean_value);
VaultJcsModelError vault_jcs_model_init_integer(VaultJcsModelValue* value, int64_t integer_value);
VaultJcsModelError vault_jcs_model_init_string(VaultJcsModelValue* value, const char* string_value);
VaultJcsModelError vault_jcs_model_init_array(VaultJcsModelValue* value, const VaultJcsModelValue* elements, size_t count);
VaultJcsModelError vault_jcs_model_init_object(VaultJcsModelValue* value, const VaultJcsModelObjectMember* members, size_t count);
void vault_jcs_model_free(VaultJcsModelValue* value);

#ifdef __cplusplus
}
#endif

#endif /* VAULT_JCS_MODEL_H */
