#include "vault_jcs_model.h"
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>
#include <stdio.h>

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

    if (count > SIZE_MAX / sizeof(VaultJcsModelValue)) {
        return VAULT_JCS_MODEL_ERROR_MEMORY;
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

    if (count > SIZE_MAX / sizeof(VaultJcsModelObjectMember)) {
        return VAULT_JCS_MODEL_ERROR_MEMORY;
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

// --- Internal Serializer Seed ---

typedef struct {
    char* data;
    size_t length;
    size_t capacity;
    VaultJcsModelError error;
} ModelStringBuffer;

static void model_buf_init(ModelStringBuffer* buf) {
    buf->capacity = 64;
    buf->length = 0;
    buf->data = (char*)malloc(buf->capacity);
    if (!buf->data) {
        buf->error = VAULT_JCS_MODEL_ERROR_MEMORY;
    } else {
        buf->error = VAULT_JCS_MODEL_OK;
        buf->data[0] = '\0';
    }
}

static void model_buf_append_len(ModelStringBuffer* buf, const char* str, size_t len) {
    if (buf->error != VAULT_JCS_MODEL_OK) return;

    if (len > SIZE_MAX - buf->length - 1) {
        buf->error = VAULT_JCS_MODEL_ERROR_MEMORY;
        return;
    }

    size_t required = buf->length + len + 1;
    if (required > buf->capacity) {
        size_t new_cap = buf->capacity;
        while (new_cap < required) {
            if (new_cap > SIZE_MAX / 2) {
                buf->error = VAULT_JCS_MODEL_ERROR_MEMORY;
                return;
            }
            new_cap *= 2;
        }
        char* new_data = (char*)realloc(buf->data, new_cap);
        if (!new_data) {
            buf->error = VAULT_JCS_MODEL_ERROR_MEMORY;
            return;
        }
        buf->data = new_data;
        buf->capacity = new_cap;
    }
    memcpy(buf->data + buf->length, str, len);
    buf->length += len;
    buf->data[buf->length] = '\0';
}

static void model_buf_append(ModelStringBuffer* buf, const char* str) {
    model_buf_append_len(buf, str, strlen(str));
}

static void model_buf_append_char(ModelStringBuffer* buf, char c) {
    model_buf_append_len(buf, &c, 1);
}

static void model_buf_free(ModelStringBuffer* buf) {
    if (buf->data) {
        free(buf->data);
        buf->data = NULL;
    }
}

static void model_serialize_string(ModelStringBuffer* buf, const char* str) {
    model_buf_append_char(buf, '"');
    const char* p = str;
    while (*p) {
        unsigned char c = (unsigned char)*p;
        if (c == '"') { model_buf_append(buf, "\\\""); }
        else if (c == '\\') { model_buf_append(buf, "\\\\"); }
        else if (c == '\b') { model_buf_append(buf, "\\b"); }
        else if (c == '\f') { model_buf_append(buf, "\\f"); }
        else if (c == '\n') { model_buf_append(buf, "\\n"); }
        else if (c == '\r') { model_buf_append(buf, "\\r"); }
        else if (c == '\t') { model_buf_append(buf, "\\t"); }
        else if (c < 0x20) {
            char hex[7];
            snprintf(hex, sizeof(hex), "\\u%04x", c);
            model_buf_append(buf, hex);
        } else {
            model_buf_append_char(buf, *p);
        }
        p++;
    }
    model_buf_append_char(buf, '"');
}

// UTF-8 to UTF-16 Code Unit Iterator
typedef struct {
    const uint8_t* p;
    uint32_t pending_surrogate;
} Utf16Iterator;

static void iter_init(Utf16Iterator* it, const char* str) {
    it->p = (const uint8_t*)str;
    it->pending_surrogate = 0;
}

static uint32_t iter_next(Utf16Iterator* it) {
    if (it->pending_surrogate != 0) {
        uint32_t cu = it->pending_surrogate;
        it->pending_surrogate = 0;
        return cu;
    }

    if (*it->p == 0) {
        return 0; // EOF
    }

    uint8_t b0 = *it->p++;
    uint32_t cp = 0;
    int extra = 0;

    if (b0 < 0x80) {
        return b0;
    } else if ((b0 & 0xE0) == 0xC0) {
        cp = b0 & 0x1F;
        extra = 1;
    } else if ((b0 & 0xF0) == 0xE0) {
        cp = b0 & 0x0F;
        extra = 2;
    } else if ((b0 & 0xF8) == 0xF0) {
        cp = b0 & 0x07;
        extra = 3;
    } else {
        return 0xFFFFFFFF; // Invalid UTF-8
    }

    for (int i = 0; i < extra; i++) {
        uint8_t b = *it->p;
        if ((b & 0xC0) != 0x80) return 0xFFFFFFFF; // Invalid UTF-8
        it->p++;
        cp = (cp << 6) | (b & 0x3F);
    }

    if (extra == 1 && cp < 0x80) return 0xFFFFFFFF; // Overlong
    if (extra == 2 && cp < 0x800) return 0xFFFFFFFF; // Overlong
    if (extra == 3 && cp < 0x10000) return 0xFFFFFFFF; // Overlong
    if (cp > 0x10FFFF) return 0xFFFFFFFF; // Out of range
    if (cp >= 0xD800 && cp <= 0xDFFF) return 0xFFFFFFFF; // Surrogate in UTF-8

    if (cp <= 0xFFFF) {
        return cp;
    } else {
        cp -= 0x10000;
        uint32_t high = 0xD800 | (cp >> 10);
        uint32_t low = 0xDC00 | (cp & 0x3FF);
        it->pending_surrogate = low;
        return high;
    }
}

static bool is_valid_utf8_for_utf16_ordering(const char* s) {
    Utf16Iterator it;
    iter_init(&it, s);
    uint32_t cu;
    while ((cu = iter_next(&it)) != 0) {
        if (cu == 0xFFFFFFFF) return false;
    }
    return true;
}

static int compare_utf16_strings(const char* a, const char* b) {
    Utf16Iterator ita, itb;
    iter_init(&ita, a);
    iter_init(&itb, b);

    while (1) {
        uint32_t cua = iter_next(&ita);
        uint32_t cub = iter_next(&itb);

        if (cua == 0xFFFFFFFF || cub == 0xFFFFFFFF) {
            // Invalid UTF-8. Pre-validation must prevent this.
            // If it occurs, return 0 to maintain sort stability without silent fallback to arbitrary byte comparison.
            return 0;
        }

        if (cua != cub) {
            return (cua < cub) ? -1 : 1;
        }
        if (cua == 0) return 0; // Both reached EOF
    }
}

static int model_compare_members(const void* a, const void* b) {
    const VaultJcsModelObjectMember* ma = *(const VaultJcsModelObjectMember**)a;
    const VaultJcsModelObjectMember* mb = *(const VaultJcsModelObjectMember**)b;
    return compare_utf16_strings(ma->key, mb->key);
}

static void model_serialize_value(ModelStringBuffer* buf, const VaultJcsModelValue* val) {
    if (buf->error != VAULT_JCS_MODEL_OK) return;

    switch (val->type) {
        case VAULT_JCS_MODEL_TYPE_NULL:
            model_buf_append(buf, "null");
            break;
        case VAULT_JCS_MODEL_TYPE_BOOLEAN:
            if (val->value.boolean_value) {
                model_buf_append(buf, "true");
            } else {
                model_buf_append(buf, "false");
            }
            break;
        case VAULT_JCS_MODEL_TYPE_INTEGER: {
            char int_str[32];
            snprintf(int_str, sizeof(int_str), "%" PRId64, val->value.integer_value);
            model_buf_append(buf, int_str);
            break;
        }
        case VAULT_JCS_MODEL_TYPE_STRING:
            if (!val->value.string_value) {
                buf->error = VAULT_JCS_MODEL_ERROR_SERIALIZE;
                return;
            }
            if (!is_valid_utf8_for_utf16_ordering(val->value.string_value)) {
                buf->error = VAULT_JCS_MODEL_ERROR_INVALID_ARG;
                return;
            }
            model_serialize_string(buf, val->value.string_value);
            break;
        case VAULT_JCS_MODEL_TYPE_ARRAY:
            if (val->value.array_value.count > 0 && !val->value.array_value.elements) {
                buf->error = VAULT_JCS_MODEL_ERROR_SERIALIZE;
                return;
            }
            model_buf_append_char(buf, '[');
            for (size_t i = 0; i < val->value.array_value.count; i++) {
                if (i > 0) model_buf_append_char(buf, ',');
                model_serialize_value(buf, &val->value.array_value.elements[i]);
            }
            model_buf_append_char(buf, ']');
            break;
        case VAULT_JCS_MODEL_TYPE_OBJECT: {
            if (val->value.object_value.count > 0 && !val->value.object_value.members) {
                buf->error = VAULT_JCS_MODEL_ERROR_SERIALIZE;
                return;
            }
            for (size_t i = 0; i < val->value.object_value.count; i++) {
                if (!val->value.object_value.members[i].key) {
                    buf->error = VAULT_JCS_MODEL_ERROR_SERIALIZE;
                    return;
                }
            }
            model_buf_append_char(buf, '{');
            size_t count = val->value.object_value.count;
            if (count > 0) {
                if (count > SIZE_MAX / sizeof(VaultJcsModelObjectMember*)) {
                    buf->error = VAULT_JCS_MODEL_ERROR_MEMORY;
                    return;
                }
                const VaultJcsModelObjectMember** sorted = (const VaultJcsModelObjectMember**)malloc(count * sizeof(VaultJcsModelObjectMember*));
                if (!sorted) {
                    buf->error = VAULT_JCS_MODEL_ERROR_MEMORY;
                    return;
                }
                for (size_t i = 0; i < count; i++) {
                    sorted[i] = &val->value.object_value.members[i];
                }

                // Pre-validate all keys to be valid UTF-8
                for (size_t i = 0; i < count; i++) {
                    if (!is_valid_utf8_for_utf16_ordering(sorted[i]->key)) {
                        buf->error = VAULT_JCS_MODEL_ERROR_INVALID_ARG;
                        break;
                    }
                }

                if (buf->error != VAULT_JCS_MODEL_OK) {
                    free(sorted);
                    return;
                }

                qsort(sorted, count, sizeof(VaultJcsModelObjectMember*), model_compare_members);

                for (size_t i = 0; i < count; i++) {
                    if (i > 0) model_buf_append_char(buf, ',');
                    model_serialize_string(buf, sorted[i]->key);
                    model_buf_append_char(buf, ':');
                    model_serialize_value(buf, &sorted[i]->value);
                }
                free(sorted);
            }
            model_buf_append_char(buf, '}');
            break;
        }
        default:
            buf->error = VAULT_JCS_MODEL_ERROR_SERIALIZE;
            return;
    }
}

VaultJcsModelError vault_jcs_model_serialize(const VaultJcsModelValue* value, char** output) {
    if (!value || !output) {
        if (output) *output = NULL;
        return VAULT_JCS_MODEL_ERROR_INVALID_ARG;
    }

    ModelStringBuffer buf;
    model_buf_init(&buf);

    model_serialize_value(&buf, value);

    if (buf.error != VAULT_JCS_MODEL_OK) {
        VaultJcsModelError err = buf.error;
        model_buf_free(&buf);
        *output = NULL;
        return err;
    }

    *output = buf.data;
    return VAULT_JCS_MODEL_OK;
}
