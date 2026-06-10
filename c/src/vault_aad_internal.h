#ifndef VAULT_AAD_INTERNAL_H
#define VAULT_AAD_INTERNAL_H

/*
 * Internal scaffold helpers for deterministic AAD construction.
 *
 * These functions allocate and return a dynamically allocated NUL-terminated
 * string. The caller is responsible for freeing the returned string using free().
 * Returns NULL on error.
 */

char* vault_aad_wrap_database_key_v1(const char* wrapped_kid, const char* wrapping_kid);

char* vault_aad_wrap_record_key_v1(const char* wrapped_kid, const char* wrapping_kid);

char* vault_aad_record_payload_v1(const char* object_uuid, const char* schema_uuid,
                                  const char* content_type, const char* kid, const char* alg);

#endif /* VAULT_AAD_INTERNAL_H */
