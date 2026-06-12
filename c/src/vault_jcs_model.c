#include "vault_jcs_model.h"
#include <stdlib.h>
#include <string.h>

#define VAULT_JCS_SAFE_INTEGER_MIN (-9007199254740991LL)
#define VAULT_JCS_SAFE_INTEGER_MAX (9007199254740991LL)

static char* internal_strdup(const char* str) {
    if (!str) {
        return NULL;
    }
    size_t len = strlen(str);
    char* copy = (char*)malloc(len + 1);
    if (copy) {
        memcpy(copy, str, len + 1);
    }
    return copy;
}

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

static VaultJcsModelError vault_jcs_model_copy(VaultJcsModelValue* dest, const VaultJcsModelValue* src);

VaultJcsModelError vault_jcs_model_init_string(VaultJcsModelValue* value, const char* string_value) {
    if (!value || !string_value) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    char* copy = internal_strdup(string_value);
    if (!copy) {
        return VAULT_JCS_MODEL_ERROR_MEMORY;
    }

    value->type = VAULT_JCS_MODEL_TYPE_STRING;
    value->value.string_value = copy;
    return VAULT_JCS_MODEL_OK;
}

VaultJcsModelError vault_jcs_model_init_array(VaultJcsModelValue* value, const VaultJcsModelValue* elements, size_t count) {
    if (!value) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }
    if (count > 0 && !elements) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    VaultJcsModelValue* copy = NULL;
    if (count > 0) {
        copy = (VaultJcsModelValue*)malloc(count * sizeof(VaultJcsModelValue));
        if (!copy) {
            return VAULT_JCS_MODEL_ERROR_MEMORY;
        }

        for (size_t i = 0; i < count; ++i) {
            VaultJcsModelError err = vault_jcs_model_copy(&copy[i], &elements[i]);
            if (err != VAULT_JCS_MODEL_OK) {
                // Cleanup on failure
                for (size_t j = 0; j < i; ++j) {
                    vault_jcs_model_free(&copy[j]);
                }
                free(copy);
                return err;
            }
        }
    }

    value->type = VAULT_JCS_MODEL_TYPE_ARRAY;
    value->value.array_value.elements = copy;
    value->value.array_value.count = count;
    return VAULT_JCS_MODEL_OK;
}

VaultJcsModelError vault_jcs_model_init_object(VaultJcsModelValue* value, const VaultJcsModelObjectMember* members, size_t count) {
    if (!value) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }
    if (count > 0 && !members) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    // Check for NULL keys and duplicate keys
    for (size_t i = 0; i < count; ++i) {
        if (!members[i].key) {
            return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
        }
        for (size_t j = i + 1; j < count; ++j) {
            if (members[j].key && strcmp(members[i].key, members[j].key) == 0) {
                return VAULT_JCS_MODEL_ERROR_DUPLICATE_KEY;
            }
        }
    }

    VaultJcsModelObjectMember* copy = NULL;
    if (count > 0) {
        copy = (VaultJcsModelObjectMember*)malloc(count * sizeof(VaultJcsModelObjectMember));
        if (!copy) {
            return VAULT_JCS_MODEL_ERROR_MEMORY;
        }

        for (size_t i = 0; i < count; ++i) {
            copy[i].key = internal_strdup(members[i].key);
            if (!copy[i].key) {
                // Cleanup on memory failure
                for (size_t j = 0; j < i; ++j) {
                    free(copy[j].key);
                    vault_jcs_model_free(&copy[j].value);
                }
                free(copy);
                return VAULT_JCS_MODEL_ERROR_MEMORY;
            }

            VaultJcsModelError err = vault_jcs_model_copy(&copy[i].value, &members[i].value);
            if (err != VAULT_JCS_MODEL_OK) {
                // Cleanup on failure
                free(copy[i].key);
                for (size_t j = 0; j < i; ++j) {
                    free(copy[j].key);
                    vault_jcs_model_free(&copy[j].value);
                }
                free(copy);
                return err;
            }
        }
    }

    value->type = VAULT_JCS_MODEL_TYPE_OBJECT;
    value->value.object_value.members = copy;
    value->value.object_value.count = count;
    return VAULT_JCS_MODEL_OK;
}

void vault_jcs_model_free(VaultJcsModelValue* value) {
    if (!value) {
        return;
    }

    if (value->type == VAULT_JCS_MODEL_TYPE_STRING && value->value.string_value) {
        free(value->value.string_value);
    } else if (value->type == VAULT_JCS_MODEL_TYPE_ARRAY) {
        if (value->value.array_value.elements) {
            for (size_t i = 0; i < value->value.array_value.count; ++i) {
                vault_jcs_model_free(&value->value.array_value.elements[i]);
            }
            free(value->value.array_value.elements);
        }
    } else if (value->type == VAULT_JCS_MODEL_TYPE_OBJECT) {
        if (value->value.object_value.members) {
            for (size_t i = 0; i < value->value.object_value.count; ++i) {
                free(value->value.object_value.members[i].key);
                vault_jcs_model_free(&value->value.object_value.members[i].value);
            }
            free(value->value.object_value.members);
        }
    }

    // Clear state
    value->type = VAULT_JCS_MODEL_TYPE_NULL;
    value->value.string_value = NULL;
}

static VaultJcsModelError vault_jcs_model_copy(VaultJcsModelValue* dest, const VaultJcsModelValue* src) {
    if (!dest || !src) {
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    switch (src->type) {
        case VAULT_JCS_MODEL_TYPE_NULL:
            return vault_jcs_model_init_null(dest);
        case VAULT_JCS_MODEL_TYPE_BOOLEAN:
            return vault_jcs_model_init_boolean(dest, src->value.boolean_value);
        case VAULT_JCS_MODEL_TYPE_INTEGER:
            return vault_jcs_model_init_integer(dest, src->value.integer_value);
        case VAULT_JCS_MODEL_TYPE_STRING:
            return vault_jcs_model_init_string(dest, src->value.string_value);
        case VAULT_JCS_MODEL_TYPE_ARRAY:
            return vault_jcs_model_init_array(dest, src->value.array_value.elements, src->value.array_value.count);
        case VAULT_JCS_MODEL_TYPE_OBJECT:
            return vault_jcs_model_init_object(dest, src->value.object_value.members, src->value.object_value.count);
        default:
            return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }
}
