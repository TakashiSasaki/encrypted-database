#include "vault_jcs_model.hpp"
#include <sstream>
#include <iomanip>
#include <algorithm>

namespace vault {
namespace jcs {

static void serialize_string(std::string& out, const std::string& str) {
    out.push_back('"');
    for (char c : str) {
        unsigned char uc = static_cast<unsigned char>(c);
        if (uc == '"') { out.append("\\\""); }
        else if (uc == '\\') { out.append("\\\\"); }
        else if (uc == '\b') { out.append("\\b"); }
        else if (uc == '\f') { out.append("\\f"); }
        else if (uc == '\n') { out.append("\\n"); }
        else if (uc == '\r') { out.append("\\r"); }
        else if (uc == '\t') { out.append("\\t"); }
        else if (uc < 0x20) {
            std::ostringstream hex;
            hex << "\\u" << std::hex << std::setw(4) << std::setfill('0') << static_cast<int>(uc);
            out.append(hex.str());
        } else {
            out.push_back(c);
        }
    }
    out.push_back('"');
}

static ModelError serialize_value(std::string& out, const ModelValue& val) {
    switch (val.type()) {
        case ModelType::Null:
            out.append("null");
            break;
        case ModelType::Boolean:
            if (val.as_boolean()) {
                out.append("true");
            } else {
                out.append("false");
            }
            break;
        case ModelType::Integer:
            out.append(std::to_string(val.as_integer()));
            break;
        case ModelType::String:
            serialize_string(out, val.as_string());
            break;
        case ModelType::Array: {
            out.push_back('[');
            const auto& arr = val.as_array();
            for (size_t i = 0; i < arr.size(); ++i) {
                if (i > 0) out.push_back(',');
                ModelError err = serialize_value(out, arr[i]);
                if (err != ModelError::OK) return err;
            }
            out.push_back(']');
            break;
        }
        case ModelType::Object: {
            out.push_back('{');
            const auto& obj = val.as_object();
            if (!obj.empty()) {
                std::vector<const ObjectMember*> sorted;
                sorted.reserve(obj.size());
                for (size_t i = 0; i < obj.size(); ++i) {
                    sorted.push_back(&obj[i]);
                }

                // Note: This simple std::string ordering is a scaffold limitation
                // and does not implement full RFC 8785 UTF-16 key ordering.
                std::sort(sorted.begin(), sorted.end(), [](const ObjectMember* a, const ObjectMember* b) {
                    return a->first < b->first;
                });

                for (size_t i = 0; i < sorted.size(); ++i) {
                    if (i > 0) out.push_back(',');
                    serialize_string(out, sorted[i]->first);
                    out.push_back(':');
                    ModelError err = serialize_value(out, sorted[i]->second);
                    if (err != ModelError::OK) return err;
                }
            }
            out.push_back('}');
            break;
        }
        default:
            return ModelError::SERIALIZE_ERROR;
    }
    return ModelError::OK;
}

Result<ModelValue> ModelValue::make_null() {
    return Result<ModelValue>::ok(ModelValue(ModelType::Null, std::monostate{}));
}

Result<ModelValue> ModelValue::make_boolean(bool value) {
    return Result<ModelValue>::ok(ModelValue(ModelType::Boolean, value));
}

Result<ModelValue> ModelValue::make_integer(int64_t value) {
    if (value < SAFE_INTEGER_MIN || value > SAFE_INTEGER_MAX) {
        return Result<ModelValue>::err(ModelError::UNSAFE_INTEGER);
    }
    return Result<ModelValue>::ok(ModelValue(ModelType::Integer, value));
}

Result<ModelValue> ModelValue::make_string(std::string value) {
    // Check for embedded NUL
    if (value.find('\0') != std::string::npos) {
        return Result<ModelValue>::err(ModelError::EMBEDDED_NUL_UNSUPPORTED);
    }
    return Result<ModelValue>::ok(ModelValue(ModelType::String, std::move(value)));
}

Result<ModelValue> ModelValue::make_array(ArrayValue elements) {
    auto ptr = std::make_shared<ArrayValue>(std::move(elements));
    return Result<ModelValue>::ok(ModelValue(ModelType::Array, ptr));
}

Result<ModelValue> ModelValue::make_object(ObjectValue members) {
    // Check for duplicate keys using simple O(N^2) comparison for this scaffold
    for (size_t i = 0; i < members.size(); ++i) {
        if (members[i].first.find('\0') != std::string::npos) {
            return Result<ModelValue>::err(ModelError::EMBEDDED_NUL_UNSUPPORTED);
        }
        for (size_t j = i + 1; j < members.size(); ++j) {
            if (members[i].first == members[j].first) {
                return Result<ModelValue>::err(ModelError::DUPLICATE_KEY);
            }
        }
    }

    auto ptr = std::make_shared<ObjectValue>(std::move(members));
    return Result<ModelValue>::ok(ModelValue(ModelType::Object, ptr));
}

Result<std::string> ModelValue::serialize() const {
    std::string out;
    ModelError err = serialize_value(out, *this);
    if (err != ModelError::OK) {
        return Result<std::string>::err(err);
    }
    return Result<std::string>::ok(std::move(out));
}

} // namespace jcs
} // namespace vault
