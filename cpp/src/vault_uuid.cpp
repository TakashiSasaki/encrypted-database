#include "vault_uuid_internal.hpp"

namespace vault {
namespace uuid {

static bool is_hex(char c) {
    return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'f');
}

bool is_valid(std::string_view uuid) {
    if (uuid.length() != 36) {
        return false;
    }

    for (size_t i = 0; i < 36; ++i) {
        if (i == 8 || i == 13 || i == 18 || i == 23) {
            if (uuid[i] != '-') {
                return false;
            }
        } else if (i == 14) {
            // Version nibble: [1-8]
            if (uuid[i] < '1' || uuid[i] > '8') {
                return false;
            }
        } else if (i == 19) {
            // Variant nibble: [8, 9, a, b]
            if (uuid[i] != '8' && uuid[i] != '9' && uuid[i] != 'a' && uuid[i] != 'b') {
                return false;
            }
        } else {
            // Hex digits
            if (!is_hex(uuid[i])) {
                return false;
            }
        }
    }

    return true;
}

} // namespace uuid
} // namespace vault
