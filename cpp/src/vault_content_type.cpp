#include "vault_content_type_internal.hpp"

namespace vault {
namespace content_type {

bool is_valid(std::string_view content_type) {
    if (content_type.empty()) {
        return false;
    }

    int slash_count = 0;
    int pre_slash_len = 0;
    int post_slash_len = 0;

    for (char ch : content_type) {
        auto c = static_cast<unsigned char>(ch);

        // Reject control characters 0x00 - 0x1F and 0x7F
        if (c < 0x20 || c == 0x7f) {
            return false;
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
        return false;
    }

    if (pre_slash_len == 0 || post_slash_len == 0) {
        return false;
    }

    return true;
}

} // namespace content_type
} // namespace vault
