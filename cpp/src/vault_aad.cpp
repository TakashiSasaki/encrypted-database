#include "vault_aad_internal.hpp"

namespace vault {
namespace aad {

std::string wrap_database_key_v1(const std::string& wrapped_kid, const std::string& wrapping_kid) {
    // Format: {"aad_policy":"wrap-database-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    return "{\"aad_policy\":\"wrap-database-key-v1\",\"v\":1,\"wrapped_kid\":\"" +
           wrapped_kid + "\",\"wrapping_kid\":\"" + wrapping_kid + "\"}";
}

std::string wrap_record_key_v1(const std::string& wrapped_kid, const std::string& wrapping_kid) {
    // Format: {"aad_policy":"wrap-record-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    return "{\"aad_policy\":\"wrap-record-key-v1\",\"v\":1,\"wrapped_kid\":\"" +
           wrapped_kid + "\",\"wrapping_kid\":\"" + wrapping_kid + "\"}";
}

std::string record_payload_v1(const std::string& object_uuid, const std::string& schema_uuid,
                              const std::string& content_type, const std::string& kid, const std::string& alg) {
    // Format: {"aad_policy":"record-payload-v1","alg":"...","content_type":"...","kid":"...","object_uuid":"...","schema_uuid":"...","v":1}
    return "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"" + alg +
           "\",\"content_type\":\"" + content_type +
           "\",\"kid\":\"" + kid +
           "\",\"object_uuid\":\"" + object_uuid +
           "\",\"schema_uuid\":\"" + schema_uuid +
           "\",\"v\":1}";
}

} // namespace aad
} // namespace vault
