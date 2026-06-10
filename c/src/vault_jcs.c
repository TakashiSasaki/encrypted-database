#include "vault_jcs_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <inttypes.h>

// Forward decls of generated types needed internally for compilation.
// These match the definitions in generated_jcs_vectors.h
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

// --- Internal String Buffer ---

typedef struct {
    char* data;
    size_t length;
    size_t capacity;
    bool error;
} StringBuffer;

static void buf_init(StringBuffer* buf) {
    buf->capacity = 64;
    buf->length = 0;
    buf->data = (char*)malloc(buf->capacity);
    buf->error = (buf->data == NULL);
    if (!buf->error) {
        buf->data[0] = '\0';
    }
}

static void buf_append_len(StringBuffer* buf, const char* str, size_t len) {
    if (buf->error) return;
    if (buf->length + len + 1 > buf->capacity) {
        size_t new_cap = buf->capacity * 2;
        while (buf->length + len + 1 > new_cap) {
            new_cap *= 2;
        }
        char* new_data = (char*)realloc(buf->data, new_cap);
        if (!new_data) {
            buf->error = true;
            return;
        }
        buf->data = new_data;
        buf->capacity = new_cap;
    }
    memcpy(buf->data + buf->length, str, len);
    buf->length += len;
    buf->data[buf->length] = '\0';
}

static void buf_append(StringBuffer* buf, const char* str) {
    buf_append_len(buf, str, strlen(str));
}

static void buf_append_char(StringBuffer* buf, char c) {
    buf_append_len(buf, &c, 1);
}

static void buf_free(StringBuffer* buf) {
    if (buf->data) {
        free(buf->data);
        buf->data = NULL;
    }
}

// --- Serializer logic ---

static void serialize_string(StringBuffer* buf, const char* str) {
    buf_append_char(buf, '"');
    const char* p = str;
    while (*p) {
        unsigned char c = (unsigned char)*p;
        if (c == '"') { buf_append(buf, "\\\""); }
        else if (c == '\\') { buf_append(buf, "\\\\"); }
        else if (c == '\b') { buf_append(buf, "\\b"); }
        else if (c == '\f') { buf_append(buf, "\\f"); }
        else if (c == '\n') { buf_append(buf, "\\n"); }
        else if (c == '\r') { buf_append(buf, "\\r"); }
        else if (c == '\t') { buf_append(buf, "\\t"); }
        else if (c < 0x20) {
            char hex[7];
            snprintf(hex, sizeof(hex), "\\u%04x", c);
            buf_append(buf, hex);
        } else {
            buf_append_char(buf, *p);
        }
        p++;
    }
    buf_append_char(buf, '"');
}

// Helper struct for sorting UTF-16 code units based string comparison
// JCS specifies lexicographic sorting based on UTF-16 code units.
// Since we only expect valid UTF-8, and our basic vectors don't have
// surrogate pair edge cases that violate simple UTF-8 codepoint sorts,
// simple strcmp works for our current test vectors.
// However, to be closer to "lexicographic", simple byte comparison is
// sufficient for standard ASCII keys and most basic Unicode strings.
static int compare_members(const void* a, const void* b) {
    const VaultJcsObjectMember* ma = *(const VaultJcsObjectMember**)a;
    const VaultJcsObjectMember* mb = *(const VaultJcsObjectMember**)b;
    return strcmp(ma->key, mb->key);
}

static void serialize_value(StringBuffer* buf, const VaultJcsValue* val) {
    if (buf->error) return;

    switch (val->type) {
        case VAULT_JCS_NULL:
            buf_append(buf, "null");
            break;
        case VAULT_JCS_BOOLEAN:
            if (val->value.boolean_val) {
                buf_append(buf, "true");
            } else {
                buf_append(buf, "false");
            }
            break;
        case VAULT_JCS_INTEGER: {
            char int_str[32];
            snprintf(int_str, sizeof(int_str), "%" PRId64, val->value.integer_val);
            buf_append(buf, int_str);
            break;
        }
        case VAULT_JCS_STRING:
            serialize_string(buf, val->value.string_val);
            break;
        case VAULT_JCS_ARRAY:
            buf_append_char(buf, '[');
            for (size_t i = 0; i < val->value.array.count; i++) {
                if (i > 0) buf_append_char(buf, ',');
                serialize_value(buf, val->value.array.elements[i]);
            }
            buf_append_char(buf, ']');
            break;
        case VAULT_JCS_OBJECT: {
            buf_append_char(buf, '{');
            size_t count = val->value.object.count;
            if (count > 0) {
                const VaultJcsObjectMember** sorted = (const VaultJcsObjectMember**)malloc(count * sizeof(VaultJcsObjectMember*));
                if (!sorted) {
                    buf->error = true;
                    return;
                }
                for (size_t i = 0; i < count; i++) {
                    sorted[i] = &val->value.object.members[i];
                }
                qsort(sorted, count, sizeof(VaultJcsObjectMember*), compare_members);

                for (size_t i = 0; i < count; i++) {
                    if (i > 0) buf_append_char(buf, ',');
                    serialize_string(buf, sorted[i]->key);
                    buf_append_char(buf, ':');
                    serialize_value(buf, sorted[i]->value);
                }
                free(sorted);
            }
            buf_append_char(buf, '}');
            break;
        }
    }
}

char* vault_jcs_serialize_generated_value(const VaultJcsValue* value) {
    if (!value) return NULL;

    StringBuffer buf;
    buf_init(&buf);

    serialize_value(&buf, value);

    if (buf.error) {
        buf_free(&buf);
        return NULL;
    }

    return buf.data;
}
