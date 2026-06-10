#ifndef VAULT_UUID_INTERNAL_H
#define VAULT_UUID_INTERNAL_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * Validates that a string is a canonical lowercase UUIDv4/v7
 * according to the Storage Format V1 requirement:
 * ^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$
 *
 * Returns 1 if valid, 0 if invalid. NULL input returns 0.
 */
int vault_is_valid_uuid(const char* uuid);

#ifdef __cplusplus
}
#endif

#endif /* VAULT_UUID_INTERNAL_H */
