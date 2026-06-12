#include "vault_jcs_model.hpp"
#include <iostream>
#include <cassert>
#include <string>

using namespace vault::jcs;

void test_serialize_null() {
    auto res = ModelValue::make_null();
    assert(res.error == ModelError::OK);

    auto ser = res.value.serialize();
    assert(ser.error == ModelError::OK);
    assert(ser.value == "null");
}

void test_serialize_boolean() {
    auto res_true = ModelValue::make_boolean(true);
    assert(res_true.error == ModelError::OK);
    auto ser_true = res_true.value.serialize();
    assert(ser_true.error == ModelError::OK);
    assert(ser_true.value == "true");

    auto res_false = ModelValue::make_boolean(false);
    assert(res_false.error == ModelError::OK);
    auto ser_false = res_false.value.serialize();
    assert(ser_false.error == ModelError::OK);
    assert(ser_false.value == "false");
}

void test_serialize_integer() {
    // Zero
    auto res_zero = ModelValue::make_integer(0);
    assert(res_zero.error == ModelError::OK);
    auto ser_zero = res_zero.value.serialize();
    assert(ser_zero.error == ModelError::OK);
    assert(ser_zero.value == "0");

    // Max safe integer
    auto res_max = ModelValue::make_integer(SAFE_INTEGER_MAX);
    assert(res_max.error == ModelError::OK);
    auto ser_max = res_max.value.serialize();
    assert(ser_max.error == ModelError::OK);
    assert(ser_max.value == "9007199254740991");

    // Min safe integer
    auto res_min = ModelValue::make_integer(SAFE_INTEGER_MIN);
    assert(res_min.error == ModelError::OK);
    auto ser_min = res_min.value.serialize();
    assert(ser_min.error == ModelError::OK);
    assert(ser_min.value == "-9007199254740991");
}

void test_serialize_string() {
    // Normal string
    auto res_normal = ModelValue::make_string("hello world");
    assert(res_normal.error == ModelError::OK);
    auto ser_normal = res_normal.value.serialize();
    assert(ser_normal.error == ModelError::OK);
    assert(ser_normal.value == "\"hello world\"");

    // Escaping
    auto res_escape = ModelValue::make_string("line1\nline2\t\"quoted\"\\back");
    assert(res_escape.error == ModelError::OK);
    auto ser_escape = res_escape.value.serialize();
    assert(ser_escape.error == ModelError::OK);
    assert(ser_escape.value == "\"line1\\nline2\\t\\\"quoted\\\"\\\\back\"");

    // Control characters < 0x20
    auto res_ctrl = ModelValue::make_string("hello\x01\x1F");
    assert(res_ctrl.error == ModelError::OK);
    auto ser_ctrl = res_ctrl.value.serialize();
    assert(ser_ctrl.error == ModelError::OK);
    assert(ser_ctrl.value == "\"hello\\u0001\\u001f\"");
}

void test_serialize_array() {
    // Empty array
    auto res_empty = ModelValue::make_array(ArrayValue{});
    assert(res_empty.error == ModelError::OK);
    auto ser_empty = res_empty.value.serialize();
    assert(ser_empty.error == ModelError::OK);
    assert(ser_empty.value == "[]");

    // Mixed array
    ArrayValue elements;
    elements.push_back(ModelValue::make_null().value);
    elements.push_back(ModelValue::make_boolean(true).value);
    elements.push_back(ModelValue::make_integer(42).value);
    elements.push_back(ModelValue::make_string("test").value);

    auto res_mixed = ModelValue::make_array(std::move(elements));
    assert(res_mixed.error == ModelError::OK);
    auto ser_mixed = res_mixed.value.serialize();
    assert(ser_mixed.error == ModelError::OK);
    assert(ser_mixed.value == "[null,true,42,\"test\"]");
}

void test_serialize_object() {
    // Empty object
    auto res_empty = ModelValue::make_object(ObjectValue{});
    assert(res_empty.error == ModelError::OK);
    auto ser_empty = res_empty.value.serialize();
    assert(ser_empty.error == ModelError::OK);
    assert(ser_empty.value == "{}");

    // Object with unsorted ASCII keys to confirm sort
    ObjectValue members;
    members.push_back({"z", ModelValue::make_integer(3).value});
    members.push_back({"a", ModelValue::make_integer(1).value});
    members.push_back({"m", ModelValue::make_integer(2).value});

    auto res_obj = ModelValue::make_object(std::move(members));
    assert(res_obj.error == ModelError::OK);

    // Test immutability: object itself shouldn't be modified by serialization
    const auto& original_obj = res_obj.value.as_object();
    assert(original_obj[0].first == "z");
    assert(original_obj[1].first == "a");
    assert(original_obj[2].first == "m");

    auto ser_obj = res_obj.value.serialize();
    assert(ser_obj.error == ModelError::OK);

    // Output should be sorted by key ("a", "m", "z")
    assert(ser_obj.value == "{\"a\":1,\"m\":2,\"z\":3}");

    // Verify it's still unmodified
    assert(original_obj[0].first == "z");
    assert(original_obj[1].first == "a");
    assert(original_obj[2].first == "m");
}

void test_serialize_nested() {
    ArrayValue inner_array;
    inner_array.push_back(ModelValue::make_string("value").value);
    inner_array.push_back(ModelValue::make_null().value);

    ObjectValue members;
    members.push_back({"key", ModelValue::make_array(std::move(inner_array)).value});

    auto res = ModelValue::make_object(std::move(members));
    assert(res.error == ModelError::OK);

    auto ser = res.value.serialize();
    assert(ser.error == ModelError::OK);
    assert(ser.value == "{\"key\":[\"value\",null]}");
}

int main() {
    std::cout << "Running C++ JCS model serializer tests..." << std::endl;
    test_serialize_null();
    test_serialize_boolean();
    test_serialize_integer();
    test_serialize_string();
    test_serialize_array();
    test_serialize_object();
    test_serialize_nested();
    std::cout << "C++ JCS model serializer tests passed." << std::endl;
    return 0;
}
