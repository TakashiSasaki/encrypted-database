#include "vault_aad_internal.hpp"
#include <iomanip>
#include <sstream>

namespace vault {
namespace aad {

static std::string escape_json_string(const std::string& input) {
    std::ostringstream oss;
    for (unsigned char c : input) {
        if (c == '"') {
            oss << "\\\"";
        } else if (c == '\\') {
            oss << "\\\\";
        } else if (c < 0x20) {
            if (c == '\b') oss << "\\b";
            else if (c == '\f') oss << "\\f";
            else if (c == '\n') oss << "\\n";
            else if (c == '\r') oss << "\\r";
            else if (c == '\t') oss << "\\t";
            else {
                oss << "\\u" << std::hex << std::setw(4) << std::setfill('0') << (int)c;
            }
        } else {
            oss << c;
        }
    }
    return oss.str();
}

std::string wrap_database_key_v1(const std::string& wrapped_kid, const std::string& wrapping_kid) {
    std::string esc_wrapped_kid = escape_json_string(wrapped_kid);
    std::string esc_wrapping_kid = escape_json_string(wrapping_kid);

    // Format: {"aad_policy":"wrap-database-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    return "{\"aad_policy\":\"wrap-database-key-v1\",\"v\":1,\"wrapped_kid\":\"" +
           esc_wrapped_kid + "\",\"wrapping_kid\":\"" + esc_wrapping_kid + "\"}";
}

std::string wrap_record_key_v1(const std::string& wrapped_kid, const std::string& wrapping_kid) {
    std::string esc_wrapped_kid = escape_json_string(wrapped_kid);
    std::string esc_wrapping_kid = escape_json_string(wrapping_kid);

    // Format: {"aad_policy":"wrap-record-key-v1","v":1,"wrapped_kid":"...","wrapping_kid":"..."}
    return "{\"aad_policy\":\"wrap-record-key-v1\",\"v\":1,\"wrapped_kid\":\"" +
           esc_wrapped_kid + "\",\"wrapping_kid\":\"" + esc_wrapping_kid + "\"}";
}

std::string record_payload_v1(const std::string& object_uuid, const std::string& schema_uuid,
                              const std::string& content_type, const std::string& kid, const std::string& alg) {
    std::string esc_object_uuid = escape_json_string(object_uuid);
    std::string esc_schema_uuid = escape_json_string(schema_uuid);
    std::string esc_content_type = escape_json_string(content_type);
    std::string esc_kid = escape_json_string(kid);
    std::string esc_alg = escape_json_string(alg);

    // Format: {"aad_policy":"record-payload-v1","alg":"...","content_type":"...","kid":"...","object_uuid":"...","schema_uuid":"...","v":1}
    return "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"" + esc_alg +
           "\",\"content_type\":\"" + esc_content_type +
           "\",\"kid\":\"" + esc_kid +
           "\",\"object_uuid\":\"" + esc_object_uuid +
           "\",\"schema_uuid\":\"" + esc_schema_uuid +
           "\",\"v\":1}";
}

} // namespace aad
} // namespace vault
