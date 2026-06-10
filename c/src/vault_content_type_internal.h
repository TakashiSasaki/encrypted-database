#ifndef VAULT_CONTENT_TYPE_INTERNAL_H
#define VAULT_CONTENT_TYPE_INTERNAL_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Validates the basic shape of a content-type string as an internal boundary check.
 * This is a minimal scaffold rule, not a full MIME parser.
 *
 * It enforces:
 * - non-NULL and non-empty string.
 * - exactly one '/' character.
 * - non-empty parts before and after the '/'.
 * - absence of ASCII control characters (0x00 - 0x1F) and DEL (0x7F).
 *
 * Returns 1 if valid, 0 if invalid. NULL input returns 0.
 */
int vault_is_valid_content_type(const char* content_type);

#ifdef __cplusplus
}
#endif

#endif /* VAULT_CONTENT_TYPE_INTERNAL_H */
