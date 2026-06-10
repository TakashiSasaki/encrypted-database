#include "vault_aad_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Minimal JSON string escaper. Allocates a new string. Caller must free.
// Escapes double quotes and backslashes.
// Note: UUIDs and ALGs are constrained, but content_type might have quotes.
static char* escape_json_string(const char* input) {
    if (!input) return NULL;
    size_t len = strlen(input);
    size_t esc_count = 0;
    for (size_t i = 0; i < len; ++i) {
        if (input[i] == '"' || input[i] == '\\' || input[i] < 0x20) {
            // Note: We'll implement basic escaping for " and \.
            // Control chars < 0x20 in content_type are generally rejected by format validators,
            // but for safety in this scaffold, we just count them.
            // Proper JCS requires \uXXXX for control chars, but for our limited AAD context,
            // escaping " and \ covers the valid input surface (e.g. `application/foo; note="x"`).
            esc_count++;
        }
    }

    // Worst case, control chars might need 6 bytes (\u00xx), but we'll do simple 2-byte escapes for " and \
    // and assume control chars are not present in valid metadata.
    // If we need strict \u00xx, we allocate 6 bytes per escape.
    char* out = (char*)malloc(len + esc_count * 5 + 1);
    if (!out) return NULL;

    size_t j = 0;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)input[i];
        if (c == '"') {
            out[j++] = '\\'; out[j++] = '"';
        } else if (c == '\\') {
            out[j++] = '\\'; out[j++] = '\\';
        } else if (c < 0x20) {
            if (c == '\b') { out[j++] = '\\'; out[j++] = 'b'; }
            else if (c == '\f') { out[j++] = '\\'; out[j++] = 'f'; }
            else if (c == '\n') { out[j++] = '\\'; out[j++] = 'n'; }
            else if (c == '\r') { out[j++] = '\\'; out[j++] = 'r'; }
            else if (c == '\t') { out[j++] = '\\'; out[j++] = 't'; }
            else {
                j += sprintf(out + j, "\\u%04x", c);
            }
        } else {
            out[j++] = c;
        }
    }
    out[j] = '\0';
    return out;
}

char* vault_aad_wrap_database_key_v1(const char* wrapped_kid, const char* wrapping_kid) {
    if (!wrapped_kid || !wrapping_kid) return NULL;

    // Format: {"aad_policy":"wrap-database-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    const char* fmt = "{\"aad_policy\":\"wrap-database-key-v1\",\"v\":1,\"wrapped_kid\":\"%s\",\"wrapping_kid\":\"%s\"}";

    int size = snprintf(NULL, 0, fmt, wrapped_kid, wrapping_kid);
    if (size < 0) return NULL;

    char* buf = (char*)malloc(size + 1);
    if (!buf) return NULL;

    snprintf(buf, size + 1, fmt, wrapped_kid, wrapping_kid);
    return buf;
}

char* vault_aad_wrap_record_key_v1(const char* wrapped_kid, const char* wrapping_kid) {
    if (!wrapped_kid || !wrapping_kid) return NULL;

    // Format: {"aad_policy":"wrap-record-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    const char* fmt = "{\"aad_policy\":\"wrap-record-key-v1\",\"v\":1,\"wrapped_kid\":\"%s\",\"wrapping_kid\":\"%s\"}";

    int size = snprintf(NULL, 0, fmt, wrapped_kid, wrapping_kid);
    if (size < 0) return NULL;

    char* buf = (char*)malloc(size + 1);
    if (!buf) return NULL;

    snprintf(buf, size + 1, fmt, wrapped_kid, wrapping_kid);
    return buf;
}

char* vault_aad_record_payload_v1(const char* object_uuid, const char* schema_uuid,
                                  const char* content_type, const char* kid, const char* alg) {
    if (!object_uuid || !schema_uuid || !content_type || !kid || !alg) return NULL;

    char* esc_content_type = escape_json_string(content_type);
    if (!esc_content_type) return NULL;

    // Format: {"aad_policy":"record-payload-v1","alg":"...","content_type":"...","kid":"...","object_uuid":"...","schema_uuid":"...","v":1}
    const char* fmt = "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"%s\",\"content_type\":\"%s\",\"kid\":\"%s\",\"object_uuid\":\"%s\",\"schema_uuid\":\"%s\",\"v\":1}";

    int size = snprintf(NULL, 0, fmt, alg, esc_content_type, kid, object_uuid, schema_uuid);
    if (size < 0) {
        free(esc_content_type);
        return NULL;
    }

    char* buf = (char*)malloc(size + 1);
    if (!buf) {
        free(esc_content_type);
        return NULL;
    }

    snprintf(buf, size + 1, fmt, alg, esc_content_type, kid, object_uuid, schema_uuid);
    free(esc_content_type);
    return buf;
}
