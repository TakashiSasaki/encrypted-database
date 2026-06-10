#include "vault_content_type_internal.h"
#include <stddef.h>

int vault_is_valid_content_type(const char* content_type) {
    if (content_type == NULL) {
        return 0;
    }

    if (content_type[0] == '\0') {
        return 0;
    }

    int slash_count = 0;
    int pre_slash_len = 0;
    int post_slash_len = 0;

    for (int i = 0; content_type[i] != '\0'; ++i) {
        unsigned char c = (unsigned char)content_type[i];

        // Reject control characters 0x00 - 0x1F and 0x7F
        if (c < 0x20 || c == 0x7f) {
            return 0;
        }

        if (c == '/') {
            slash_count++;
        } else {
            if (slash_count == 0) {
                pre_slash_len++;
            } else if (slash_count == 1) {
                post_slash_len++;
            }
        }
    }

    if (slash_count != 1) {
        return 0;
    }

    if (pre_slash_len == 0 || post_slash_len == 0) {
        return 0;
    }

    return 1;
}
