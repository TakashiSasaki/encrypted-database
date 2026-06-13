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

// UTF-8 to UTF-16 Code Unit Iterator for std::string
class Utf16Iterator {
    const char* p_;
    const char* end_;
    uint32_t pending_surrogate_;

public:
    Utf16Iterator(const std::string& s) : p_(s.data()), end_(s.data() + s.size()), pending_surrogate_(0) {}

    uint32_t next() {
        if (pending_surrogate_ != 0) {
            uint32_t cu = pending_surrogate_;
            pending_surrogate_ = 0;
            return cu;
        }

        if (p_ == end_) return 0;

        uint8_t b0 = static_cast<uint8_t>(*p_++);
        uint32_t cp = 0;
        int extra = 0;

        if (b0 < 0x80) return b0;
        else if ((b0 & 0xE0) == 0xC0) { cp = b0 & 0x1F; extra = 1; }
        else if ((b0 & 0xF0) == 0xE0) { cp = b0 & 0x0F; extra = 2; }
        else if ((b0 & 0xF8) == 0xF0) { cp = b0 & 0x07; extra = 3; }
        else return 0xFFFFFFFF; // Invalid

        if (end_ - p_ < extra) return 0xFFFFFFFF; // Truncated

        for (int i = 0; i < extra; i++) {
            uint8_t b = static_cast<uint8_t>(*p_);
            if ((b & 0xC0) != 0x80) return 0xFFFFFFFF;
            p_++;
            cp = (cp << 6) | (b & 0x3F);
        }

        if (extra == 1 && cp < 0x80) return 0xFFFFFFFF;
        if (extra == 2 && cp < 0x800) return 0xFFFFFFFF;
        if (extra == 3 && cp < 0x10000) return 0xFFFFFFFF;
        if (cp > 0x10FFFF) return 0xFFFFFFFF;
        if (cp >= 0xD800 && cp <= 0xDFFF) return 0xFFFFFFFF;

        if (cp <= 0xFFFF) return cp;

        cp -= 0x10000;
        pending_surrogate_ = 0xDC00 | (cp & 0x3FF);
        return 0xD800 | (cp >> 10);
    }
};

static bool is_valid_utf8(const std::string& s) {
    Utf16Iterator it(s);
    uint32_t cu;
    while ((cu = it.next()) != 0) {
        if (cu == 0xFFFFFFFF) return false;
    }
    return true;
}

static int compare_utf16(const std::string& a, const std::string& b) {
    Utf16Iterator ita(a);
    Utf16Iterator itb(b);

    while (true) {
        uint32_t cua = ita.next();
        uint32_t cub = itb.next();

        if (cua == 0xFFFFFFFF || cub == 0xFFFFFFFF) {
            // Invalid UTF-8. Pre-validation must prevent this.
            // If it occurs, return 0 to maintain sort stability without silent fallback to arbitrary byte comparison.
            return 0;
        }
        if (cua != cub) return (cua < cub) ? -1 : 1;
        if (cua == 0) return 0;
    }
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
                    if (!is_valid_utf8(obj[i].first)) {
                        return ModelError::INVALID_ARG;
                    }
                    sorted.push_back(&obj[i]);
                }

                std::sort(sorted.begin(), sorted.end(), [](const ObjectMember* a, const ObjectMember* b) {
                    return compare_utf16(a->first, b->first) < 0;
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
    try {
        auto ptr = std::make_shared<ArrayValue>(std::move(elements));
        return Result<ModelValue>::ok(ModelValue(ModelType::Array, ptr));
    } catch (const std::bad_alloc&) {
        return Result<ModelValue>::err(ModelError::MEMORY_ERROR);
    } catch (const std::exception&) {
        return Result<ModelValue>::err(ModelError::INVALID_ARG);
    }
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

    try {
        auto ptr = std::make_shared<ObjectValue>(std::move(members));
        return Result<ModelValue>::ok(ModelValue(ModelType::Object, ptr));
    } catch (const std::bad_alloc&) {
        return Result<ModelValue>::err(ModelError::MEMORY_ERROR);
    } catch (const std::exception&) {
        return Result<ModelValue>::err(ModelError::INVALID_ARG);
    }
}

Result<std::string> ModelValue::serialize() const {
    std::string out;
    try {
        ModelError err = serialize_value(out, *this);
        if (err != ModelError::OK) {
            return Result<std::string>::err(err);
        }
    } catch (const std::bad_alloc&) {
        return Result<std::string>::err(ModelError::MEMORY_ERROR);
    } catch (const std::exception&) {
        return Result<std::string>::err(ModelError::SERIALIZE_ERROR);
    }
    return Result<std::string>::ok(std::move(out));
}

} // namespace jcs
} // namespace vault
