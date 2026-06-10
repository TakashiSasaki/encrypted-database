#include "vault_aad_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

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

    // Format: {"aad_policy":"record-payload-v1","alg":"...","content_type":"...","kid":"...","object_uuid":"...","schema_uuid":"...","v":1}
    const char* fmt = "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"%s\",\"content_type\":\"%s\",\"kid\":\"%s\",\"object_uuid\":\"%s\",\"schema_uuid\":\"%s\",\"v\":1}";

    int size = snprintf(NULL, 0, fmt, alg, content_type, kid, object_uuid, schema_uuid);
    if (size < 0) return NULL;

    char* buf = (char*)malloc(size + 1);
    if (!buf) return NULL;

    snprintf(buf, size + 1, fmt, alg, content_type, kid, object_uuid, schema_uuid);
    return buf;
}
