#ifndef VAULT_UUID_INTERNAL_HPP
#define VAULT_UUID_INTERNAL_HPP

#include <string_view>

namespace vault {
namespace uuid {

/*
 * Validates that a string is a canonical lowercase UUIDv4/v7
 * according to the Storage Format V1 requirement:
 * ^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$
 *
 * Returns true if valid, false if invalid.
 */
bool is_valid(std::string_view uuid);

} // namespace uuid
} // namespace vault

#endif // VAULT_UUID_INTERNAL_HPP
