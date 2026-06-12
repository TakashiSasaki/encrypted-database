#include "vault_jcs_model.hpp"

namespace vault {
namespace jcs {

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
        for (size_t j = i + 1; j < members.size(); ++j) {
            if (members[i].first == members[j].first) {
                return Result<ModelValue>::err(ModelError::DUPLICATE_KEY);
            }
        }
    }

    auto ptr = std::make_shared<ObjectValue>(std::move(members));
    return Result<ModelValue>::ok(ModelValue(ModelType::Object, ptr));
}

} // namespace jcs
} // namespace vault
