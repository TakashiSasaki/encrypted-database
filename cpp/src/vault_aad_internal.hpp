#ifndef VAULT_AAD_INTERNAL_HPP
#define VAULT_AAD_INTERNAL_HPP

#include <string>

namespace vault {
namespace aad {

// Internal scaffold helpers for deterministic AAD construction.
// Returns explicitly formatted JCS canonical strings.

std::string wrap_database_key_v1(const std::string& wrapped_kid, const std::string& wrapping_kid);

std::string wrap_record_key_v1(const std::string& wrapped_kid, const std::string& wrapping_kid);

std::string record_payload_v1(const std::string& object_uuid, const std::string& schema_uuid,
                              const std::string& content_type, const std::string& kid, const std::string& alg);

} // namespace aad
} // namespace vault

#endif // VAULT_AAD_INTERNAL_HPP
