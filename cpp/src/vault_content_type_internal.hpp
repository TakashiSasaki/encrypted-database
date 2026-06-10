#ifndef VAULT_CONTENT_TYPE_INTERNAL_HPP
#define VAULT_CONTENT_TYPE_INTERNAL_HPP

#include <string_view>

namespace vault {
namespace content_type {

/*
 * Validates the basic shape of a content-type string as an internal boundary check.
 * This is a minimal scaffold rule, not a full MIME parser.
 *
 * It enforces:
 * - non-empty string.
 * - exactly one '/' character.
 * - non-empty parts before and after the '/'.
 * - absence of ASCII control characters (0x00 - 0x1F) and DEL (0x7F).
 *
 * Returns true if valid, false if invalid.
 */
bool is_valid(std::string_view content_type);

} // namespace content_type
} // namespace vault

#endif // VAULT_CONTENT_TYPE_INTERNAL_HPP
