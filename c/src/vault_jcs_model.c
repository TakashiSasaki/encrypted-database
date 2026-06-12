#include "vault_jcs_model.h"
#include <stdlib.h>
#include <string.h>

#define VAULT_JCS_SAFE_INTEGER_MIN (-9007199254740991LL)
#define VAULT_JCS_SAFE_INTEGER_MAX (9007199254740991LL)

VaultJcsModelError vault_jcs_model_init_null(VaultJcsModelValue* value) {
    if (!value) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    value->type = VAULT_JCS_MODEL_TYPE_NULL;
    return VAULT_JCS_MODEL_OK;
}

VaultJcsModelError vault_jcs_model_init_boolean(VaultJcsModelValue* value, bool boolean_value) {
    if (!value) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    value->type = VAULT_JCS_MODEL_TYPE_BOOLEAN;
    value->value.boolean_value = boolean_value;
    return VAULT_JCS_MODEL_OK;
}

VaultJcsModelError vault_jcs_model_init_integer(VaultJcsModelValue* value, int64_t integer_value) {
    if (!value) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    if (integer_value < VAULT_JCS_SAFE_INTEGER_MIN || integer_value > VAULT_JCS_SAFE_INTEGER_MAX) {
        return VAULT_JCS_MODEL_ERROR_UNSAFE_INTEGER;
    }

    value->type = VAULT_JCS_MODEL_TYPE_INTEGER;
    value->value.integer_value = integer_value;
    return VAULT_JCS_MODEL_OK;
}

VaultJcsModelError vault_jcs_model_init_string(VaultJcsModelValue* value, const char* string_value) {
    if (!value || !string_value) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    char* copy = strdup(string_value);
    if (!copy) {
        return VAULT_JCS_MODEL_ERROR_MEMORY;
    }

    value->type = VAULT_JCS_MODEL_TYPE_STRING;
    value->value.string_value = copy;
    return VAULT_JCS_MODEL_OK;
}

void vault_jcs_model_free(VaultJcsModelValue* value) {
    if (!value) {
        return;
    }

    if (value->type == VAULT_JCS_MODEL_TYPE_STRING && value->value.string_value) {
        free(value->value.string_value);
    }

    // Clear state
    value->type = VAULT_JCS_MODEL_TYPE_NULL;
    value->value.string_value = NULL;
}
