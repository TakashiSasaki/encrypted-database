#include "vault_uuid_internal.h"
#include <stddef.h>

static int is_hex(char c) {
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
}

int vault_is_valid_uuid(const char* uuid) {
    if (uuid == NULL) {
        return 0;
    }

    // Must be exactly 36 characters
    int i;
    for (i = 0; i < 36; ++i) {
        if (uuid[i] == '\0') {
            return 0; // Too short
        }

        if (i == 8 || i == 13 || i == 18 || i == 23) {
            if (uuid[i] != '-') {
                return 0;
            }
        } else if (i == 14) {
            // Version nibble: [1-8]
            if (uuid[i] < '1' || uuid[i] > '8') {
                return 0;
            }
        } else if (i == 19) {
            // Variant nibble: [8, 9, a, b]
            if (uuid[i] != '8' && uuid[i] != '9' && uuid[i] != 'a' && uuid[i] != 'b') {
                return 0;
            }
        } else {
            // Hex digits
            if (!is_hex(uuid[i])) {
                return 0; // Invalid char (e.g., uppercase hex or other chars)
            }
        }
    }

    if (uuid[36] != '\0') {
        return 0; // Too long
    }

    return 1;
}
