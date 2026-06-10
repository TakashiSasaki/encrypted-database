#include "vault_aad_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

// Minimal JSON string escaper. Allocates a new string. Caller must free.
// Uses a two-pass approach to compute the exact escaped length, then write to it.
// Escapes double quotes, backslashes, and control characters (< 0x20)
// using short escapes (\n, \t, etc) where possible, and \u00xx otherwise.
// Valid UTF-8 non-ASCII bytes are preserved.
static char* escape_json_string(const char* input) {
    if (!input) return NULL;
    size_t len = strlen(input);

    // First pass: compute exactly how long the escaped string will be
    size_t escaped_len = 0;
    for (size_t i = 0; i < len; ++i) {
        unsigned char c = (unsigned char)input[i];
        if (c == '"' || c == '\\' || c == '\b' || c == '\f' || c == '\n' || c == '\r' || c == '\t') {
            escaped_len += 2;
        } else if (c < 0x20) {
            escaped_len += 6; // \u00xx
        } else {
            escaped_len += 1;
        }
    }

    char* out = (char*)malloc(escaped_len + 1);
    if (!out) return NULL;

    // Second pass: fill the string
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
                snprintf(out + j, 7, "\\u%04x", c);
                j += 6;
            }
        } else {
            out[j++] = c;
        }
    }
    out[escaped_len] = '\0';
    return out;
}

char* vault_aad_wrap_database_key_v1(const char* wrapped_kid, const char* wrapping_kid) {
    if (!wrapped_kid || !wrapping_kid) return NULL;

    char* esc_wrapped_kid = escape_json_string(wrapped_kid);
    char* esc_wrapping_kid = escape_json_string(wrapping_kid);
    if (!esc_wrapped_kid || !esc_wrapping_kid) {
        free(esc_wrapped_kid);
        free(esc_wrapping_kid);
        return NULL;
    }

    // Format: {"aad_policy":"wrap-database-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    const char* fmt = "{\"aad_policy\":\"wrap-database-key-v1\",\"v\":1,\"wrapped_kid\":\"%s\",\"wrapping_kid\":\"%s\"}";

    int size = snprintf(NULL, 0, fmt, esc_wrapped_kid, esc_wrapping_kid);
    if (size < 0) {
        free(esc_wrapped_kid);
        free(esc_wrapping_kid);
        return NULL;
    }

    char* buf = (char*)malloc(size + 1);
    if (!buf) {
        free(esc_wrapped_kid);
        free(esc_wrapping_kid);
        return NULL;
    }

    snprintf(buf, size + 1, fmt, esc_wrapped_kid, esc_wrapping_kid);
    free(esc_wrapped_kid);
    free(esc_wrapping_kid);
    return buf;
}

char* vault_aad_wrap_record_key_v1(const char* wrapped_kid, const char* wrapping_kid) {
    if (!wrapped_kid || !wrapping_kid) return NULL;

    char* esc_wrapped_kid = escape_json_string(wrapped_kid);
    char* esc_wrapping_kid = escape_json_string(wrapping_kid);
    if (!esc_wrapped_kid || !esc_wrapping_kid) {
        free(esc_wrapped_kid);
        free(esc_wrapping_kid);
        return NULL;
    }

    // Format: {"aad_policy":"wrap-record-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    const char* fmt = "{\"aad_policy\":\"wrap-record-key-v1\",\"v\":1,\"wrapped_kid\":\"%s\",\"wrapping_kid\":\"%s\"}";

    int size = snprintf(NULL, 0, fmt, esc_wrapped_kid, esc_wrapping_kid);
    if (size < 0) {
        free(esc_wrapped_kid);
        free(esc_wrapping_kid);
        return NULL;
    }

    char* buf = (char*)malloc(size + 1);
    if (!buf) {
        free(esc_wrapped_kid);
        free(esc_wrapping_kid);
        return NULL;
    }

    snprintf(buf, size + 1, fmt, esc_wrapped_kid, esc_wrapping_kid);
    free(esc_wrapped_kid);
    free(esc_wrapping_kid);
    return buf;
}

char* vault_aad_record_payload_v1(const char* object_uuid, const char* schema_uuid,
                                  const char* content_type, const char* kid, const char* alg) {
    if (!object_uuid || !schema_uuid || !content_type || !kid || !alg) return NULL;

    char* esc_object_uuid = escape_json_string(object_uuid);
    char* esc_schema_uuid = escape_json_string(schema_uuid);
    char* esc_content_type = escape_json_string(content_type);
    char* esc_kid = escape_json_string(kid);
    char* esc_alg = escape_json_string(alg);

    if (!esc_object_uuid || !esc_schema_uuid || !esc_content_type || !esc_kid || !esc_alg) {
        free(esc_object_uuid);
        free(esc_schema_uuid);
        free(esc_content_type);
        free(esc_kid);
        free(esc_alg);
        return NULL;
    }

    // Format: {"aad_policy":"record-payload-v1","alg":"...","content_type":"...","kid":"...","object_uuid":"...","schema_uuid":"...","v":1}
    const char* fmt = "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"%s\",\"content_type\":\"%s\",\"kid\":\"%s\",\"object_uuid\":\"%s\",\"schema_uuid\":\"%s\",\"v\":1}";

    int size = snprintf(NULL, 0, fmt, esc_alg, esc_content_type, esc_kid, esc_object_uuid, esc_schema_uuid);
    if (size < 0) {
        free(esc_object_uuid);
        free(esc_schema_uuid);
        free(esc_content_type);
        free(esc_kid);
        free(esc_alg);
        return NULL;
    }

    char* buf = (char*)malloc(size + 1);
    if (!buf) {
        free(esc_object_uuid);
        free(esc_schema_uuid);
        free(esc_content_type);
        free(esc_kid);
        free(esc_alg);
        return NULL;
    }

    snprintf(buf, size + 1, fmt, esc_alg, esc_content_type, esc_kid, esc_object_uuid, esc_schema_uuid);

    free(esc_object_uuid);
    free(esc_schema_uuid);
    free(esc_content_type);
    free(esc_kid);
    free(esc_alg);
    return buf;
}
