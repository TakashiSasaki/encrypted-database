#include "vault_jcs_internal.hpp"
#include <vector>
#include <algorithm>
#include <sstream>
#include <iomanip>

// Include the C-compatible fixture layout directly
#include "vault_jcs_internal.h"

namespace vault {
namespace jcs {

static void serialize_string(std::string& out, const char* str) {
    out.push_back('"');
    const char* p = str;
    while (*p) {
        unsigned char c = static_cast<unsigned char>(*p);
        if (c == '"') { out.append("\\\""); }
        else if (c == '\\') { out.append("\\\\"); }
        else if (c == '\b') { out.append("\\b"); }
        else if (c == '\f') { out.append("\\f"); }
        else if (c == '\n') { out.append("\\n"); }
        else if (c == '\r') { out.append("\\r"); }
        else if (c == '\t') { out.append("\\t"); }
        else if (c < 0x20) {
            std::ostringstream hex;
            hex << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(c);
            out.append(hex.str());
        } else {
            out.push_back(*p);
        }
        p++;
    }
    out.push_back('"');
}

static void serialize_value(std::string& out, const VaultJcsValue& val) {
    switch (val.type) {
        case VAULT_JCS_NULL:
            out.append("null");
            break;
        case VAULT_JCS_BOOLEAN:
            if (val.value.boolean_val) {
                out.append("true");
            } else {
                out.append("false");
            }
            break;
        case VAULT_JCS_INTEGER:
            out.append(std::to_string(val.value.integer_val));
            break;
        case VAULT_JCS_STRING:
            serialize_string(out, val.value.string_val);
            break;
        case VAULT_JCS_ARRAY:
            out.push_back('[');
            for (size_t i = 0; i < val.value.array.count; i++) {
                if (i > 0) out.push_back(',');
                serialize_value(out, *val.value.array.elements[i]);
            }
            out.push_back(']');
            break;
        case VAULT_JCS_OBJECT: {
            out.push_back('{');
            size_t count = val.value.object.count;
            if (count > 0) {
                std::vector<const VaultJcsObjectMember*> sorted;
                sorted.reserve(count);
                for (size_t i = 0; i < count; i++) {
                    sorted.push_back(&val.value.object.members[i]);
                }

                std::sort(sorted.begin(), sorted.end(), [](const VaultJcsObjectMember* a, const VaultJcsObjectMember* b) {
                    return std::string(a->key) < std::string(b->key);
                });

                for (size_t i = 0; i < sorted.size(); i++) {
                    if (i > 0) out.push_back(',');
                    serialize_string(out, sorted[i]->key);
                    out.push_back(':');
                    serialize_value(out, *sorted[i]->value);
                }
            }
            out.push_back('}');
            break;
        }
    }
}

std::string serialize_generated_value(const VaultJcsValue& value) {
    std::string out;
    serialize_value(out, value);
    return out;
}

} // namespace jcs
} // namespace vault
