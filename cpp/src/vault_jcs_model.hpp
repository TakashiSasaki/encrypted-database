#ifndef VAULT_CPP_JCS_MODEL_HPP
#define VAULT_CPP_JCS_MODEL_HPP

#include <string>
#include <vector>
#include <variant>
#include <memory>
#include <stdexcept>
#include <cstdint>
#include <utility>

namespace vault {
namespace jcs {

enum class ModelError {
    OK = 0,
    INVALID_ARG,
    UNSAFE_INTEGER,
    DUPLICATE_KEY,
    EMBEDDED_NUL_UNSUPPORTED,
    SERIALIZE_ERROR,
    MEMORY_ERROR
};

// Internal model type identifier (analogous to the C enum, but mapped locally)
enum class ModelType {
    Null,
    Boolean,
    Integer,
    String,
    Array,
    Object
};

// Forward declaration for recursive types
struct ModelValue;

using ArrayValue = std::vector<ModelValue>;
using ObjectMember = std::pair<std::string, ModelValue>;
using ObjectValue = std::vector<ObjectMember>;

// Use a variant to hold the value
using ValueVariant = std::variant<
    std::monostate, // Null
    bool,           // Boolean
    int64_t,        // Integer
    std::string,    // String
    std::shared_ptr<ArrayValue>,  // Array (heap allocated to avoid incomplete type issues in variant)
    std::shared_ptr<ObjectValue>  // Object (heap allocated to avoid incomplete type issues in variant)
>;

// IEEE-754 Safe Integer bounds
constexpr int64_t SAFE_INTEGER_MIN = -9007199254740991LL;
constexpr int64_t SAFE_INTEGER_MAX = 9007199254740991LL;

// Simple struct combining a model value and an error status (Result pattern)
template <typename T>
struct Result {
    T value;
    ModelError error;

    static Result<T> ok(T&& val) {
        return Result<T>{std::move(val), ModelError::OK};
    }

    static Result<T> err(ModelError e) {
        return Result<T>{T{}, e};
    }
};

class ModelValue {
public:
    // Default constructor creates a Null value
    ModelValue() : type_(ModelType::Null), val_(std::monostate{}) {}

    // Copy and Move constructors
    // Note: Due to the use of std::shared_ptr for composite types (Array/Object),
    // default copy construction and assignment result in shallow copies.
    // This provides safe lifetime management but does not provide deep-copy value semantics.
    ModelValue(const ModelValue& other) = default;
    ModelValue(ModelValue&& other) noexcept = default;
    ModelValue& operator=(const ModelValue& other) = default;
    ModelValue& operator=(ModelValue&& other) noexcept = default;

    ModelType type() const { return type_; }

    // Accessors
    bool is_null() const { return type_ == ModelType::Null; }
    bool as_boolean() const { return std::get<bool>(val_); }
    int64_t as_integer() const { return std::get<int64_t>(val_); }
    const std::string& as_string() const { return std::get<std::string>(val_); }
    const ArrayValue& as_array() const { return *std::get<std::shared_ptr<ArrayValue>>(val_); }
    const ObjectValue& as_object() const { return *std::get<std::shared_ptr<ObjectValue>>(val_); }

    // Factories
    static Result<ModelValue> make_null();
    static Result<ModelValue> make_boolean(bool value);
    static Result<ModelValue> make_integer(int64_t value);
    static Result<ModelValue> make_string(std::string value);
    static Result<ModelValue> make_array(ArrayValue elements);
    static Result<ModelValue> make_object(ObjectValue members);

    // Serialization
    // Serializes the internal model value into a compact JSON string.
    // Note: Object key sorting currently uses simple std::string byte ordering,
    // which is a scaffold limitation and not full RFC 8785 UTF-16 key ordering.
    Result<std::string> serialize() const;

private:
    ModelType type_;
    ValueVariant val_;

    // Private constructor used by factories
    ModelValue(ModelType t, ValueVariant v) : type_(t), val_(std::move(v)) {}
};

} // namespace jcs
} // namespace vault

#endif // VAULT_CPP_JCS_MODEL_HPP
