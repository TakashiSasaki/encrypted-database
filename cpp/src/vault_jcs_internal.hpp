#ifndef VAULT_JCS_INTERNAL_HPP
#define VAULT_JCS_INTERNAL_HPP

#include <string>

// Forward declaration of the generated JCS value type from the C header
struct VaultJcsValue;

namespace vault {
namespace jcs {

/**
 * @brief Internal C++ JCS serializer scaffold.
 *
 * Serializes the generated VaultJcsValue AST to a std::string.
 * Uses the same AST structs defined for C to avoid duplicating the generator logic,
 * but implements the serialization natively in C++.
 *
 * Supported features:
 * - string escaping
 * - lexicographic object key sorting
 * - booleans, null, strings, integers, arrays, objects
 *
 * @param value The root AST node.
 * @return A std::string containing the JCS canonical representation.
 */
std::string serialize_generated_value(const VaultJcsValue& value);

} // namespace jcs
} // namespace vault

#endif // VAULT_JCS_INTERNAL_HPP
