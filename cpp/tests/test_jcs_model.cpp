#include "vault_jcs_model.hpp"
#include <iostream>
#include <cassert>
#include <string>
#include <vector>

using namespace vault::jcs;

void test_null_construction() {
    auto res = ModelValue::make_null();
    assert(res.error == ModelError::OK);
    assert(res.value.type() == ModelType::Null);
    assert(res.value.is_null());
}

void test_boolean_construction() {
    auto res1 = ModelValue::make_boolean(true);
    assert(res1.error == ModelError::OK);
    assert(res1.value.type() == ModelType::Boolean);
    assert(res1.value.as_boolean() == true);

    auto res2 = ModelValue::make_boolean(false);
    assert(res2.error == ModelError::OK);
    assert(res2.value.type() == ModelType::Boolean);
    assert(res2.value.as_boolean() == false);
}

void test_integer_construction() {
    // Test zero
    auto res1 = ModelValue::make_integer(0);
    assert(res1.error == ModelError::OK);
    assert(res1.value.type() == ModelType::Integer);
    assert(res1.value.as_integer() == 0);

    // Test max safe
    auto res2 = ModelValue::make_integer(SAFE_INTEGER_MAX);
    assert(res2.error == ModelError::OK);
    assert(res2.value.as_integer() == SAFE_INTEGER_MAX);

    // Test min safe
    auto res3 = ModelValue::make_integer(SAFE_INTEGER_MIN);
    assert(res3.error == ModelError::OK);
    assert(res3.value.as_integer() == SAFE_INTEGER_MIN);

    // Test unsafe rejection max+1
    auto res4 = ModelValue::make_integer(SAFE_INTEGER_MAX + 1);
    assert(res4.error == ModelError::UNSAFE_INTEGER);

    // Test unsafe rejection min-1
    auto res5 = ModelValue::make_integer(SAFE_INTEGER_MIN - 1);
    assert(res5.error == ModelError::UNSAFE_INTEGER);
}

void test_string_construction() {
    // Test valid string
    std::string str_val = "hello world";
    auto res1 = ModelValue::make_string(str_val);
    assert(res1.error == ModelError::OK);
    assert(res1.value.type() == ModelType::String);
    assert(res1.value.as_string() == str_val);

    // Test embedded NUL rejection
    std::string nul_str = "hello\0world";
    // We construct it safely with string size constructor to ensure NUL is embedded
    std::string true_nul_str("hello\0world", 11);
    auto res2 = ModelValue::make_string(true_nul_str);
    assert(res2.error == ModelError::EMBEDDED_NUL_UNSUPPORTED);
}

void test_array_construction() {
    // Test empty array
    auto res1 = ModelValue::make_array(ArrayValue{});
    assert(res1.error == ModelError::OK);
    assert(res1.value.type() == ModelType::Array);
    assert(res1.value.as_array().empty());

    // Test array with elements
    ArrayValue elements;
    elements.push_back(ModelValue::make_null().value);
    elements.push_back(ModelValue::make_boolean(true).value);
    elements.push_back(ModelValue::make_integer(42).value);
    elements.push_back(ModelValue::make_string("test").value);

    auto res2 = ModelValue::make_array(std::move(elements));
    assert(res2.error == ModelError::OK);
    assert(res2.value.type() == ModelType::Array);

    const auto& arr = res2.value.as_array();
    assert(arr.size() == 4);
    assert(arr[0].type() == ModelType::Null);
    assert(arr[1].type() == ModelType::Boolean && arr[1].as_boolean() == true);
    assert(arr[2].type() == ModelType::Integer && arr[2].as_integer() == 42);
    assert(arr[3].type() == ModelType::String && arr[3].as_string() == "test");
}

void test_object_construction() {
    // Test empty object
    auto res1 = ModelValue::make_object(ObjectValue{});
    assert(res1.error == ModelError::OK);
    assert(res1.value.type() == ModelType::Object);
    assert(res1.value.as_object().empty());

    // Test object with elements
    ObjectValue members;
    members.push_back({"key1", ModelValue::make_string("value1").value});
    members.push_back({"key2", ModelValue::make_integer(123).value});

    auto res2 = ModelValue::make_object(std::move(members));
    assert(res2.error == ModelError::OK);
    assert(res2.value.type() == ModelType::Object);

    const auto& obj = res2.value.as_object();
    assert(obj.size() == 2);
    assert(obj[0].first == "key1" && obj[0].second.as_string() == "value1");
    assert(obj[1].first == "key2" && obj[1].second.as_integer() == 123);

    // Test duplicate key rejection
    ObjectValue dup_members;
    dup_members.push_back({"same", ModelValue::make_null().value});
    dup_members.push_back({"same", ModelValue::make_integer(1).value});

    auto res3 = ModelValue::make_object(std::move(dup_members));
    assert(res3.error == ModelError::DUPLICATE_KEY);
    // Test object key embedded NUL rejection
    ObjectValue nul_key_members;
    std::string nul_key("hello\0world", 11);
    nul_key_members.push_back({nul_key, ModelValue::make_integer(1).value});
    auto res4 = ModelValue::make_object(std::move(nul_key_members));
    assert(res4.error == ModelError::EMBEDDED_NUL_UNSUPPORTED);
}

void test_nested_composite() {
    // Nested array inside object
    ArrayValue nested_array;
    nested_array.push_back(ModelValue::make_string("nested_string").value);

    ObjectValue members;
    members.push_back({"nested_array", ModelValue::make_array(std::move(nested_array)).value});

    auto res = ModelValue::make_object(std::move(members));
    assert(res.error == ModelError::OK);

    const auto& obj = res.value.as_object();
    assert(obj.size() == 1);
    assert(obj[0].first == "nested_array");
    assert(obj[0].second.type() == ModelType::Array);
    assert(obj[0].second.as_array()[0].as_string() == "nested_string");
}

void test_copy_and_move() {
    auto original = ModelValue::make_string("copy_test").value;

    // Copy construction
    ModelValue copied = original;
    assert(copied.type() == ModelType::String);
    assert(copied.as_string() == "copy_test");
    assert(original.as_string() == "copy_test"); // Original intact

    // Move construction
    ModelValue moved = std::move(copied);
    assert(moved.type() == ModelType::String);
    assert(moved.as_string() == "copy_test");
    // State of copied is technically unspecified/valid but moved-from,
    // for std::string typically empty but we won't strictly assert value here.

    // Test copying complex nested object to demonstrate shared_ptr semantics
    // Note: This C++ implementation uses shared_ptr for Array and Object, which provides
    // shallow copies of the collection structure. This ensures safe lifetime management
    // but does NOT provide deep-copy value semantics. Mutating the underlying collection
    // (if it were not const) would affect all copies.
    ObjectValue members;
    members.push_back({"key", ModelValue::make_integer(1).value});
    auto complex = ModelValue::make_object(std::move(members)).value;

    ModelValue complex_copy = complex;
    assert(complex_copy.as_object()[0].second.as_integer() == 1);

    // Explicitly verify they share the same underlying memory via reference comparison
    assert(&complex.as_object() == &complex_copy.as_object());
}

int main() {
    std::cout << "Running C++ JCS internal model tests..." << std::endl;
    test_null_construction();
    test_boolean_construction();
    test_integer_construction();
    test_string_construction();
    test_array_construction();
    test_object_construction();
    test_nested_composite();
    test_copy_and_move();
    std::cout << "C++ JCS internal model tests passed." << std::endl;
    return 0;
}
