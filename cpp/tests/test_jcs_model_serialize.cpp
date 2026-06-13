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

void test_serialize_object_ordering() {
    // Empty object
    auto res_empty = ModelValue::make_object(ObjectValue{});
    assert(res_empty.error == ModelError::OK);
    auto ser_empty = res_empty.value.serialize();
    assert(ser_empty.error == ModelError::OK);
    assert(ser_empty.value == "{}");

    // Object with unsorted ASCII keys to confirm sort.
    // Note: This validates only simple std::string ASCII/basic-compatible ordering.
    // It explicitly does NOT provide full RFC 8785 UTF-16 surrogate key ordering coverage.
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

void test_serialize_object_ordering_utf16() {
    // BMP non-ASCII: "あ" (U+3042), "い" (U+3044)
    ObjectValue members_bmp;
    members_bmp.push_back({"\xE3\x81\x84", ModelValue::make_integer(2).value}); // "い"
    members_bmp.push_back({"\xE3\x81\x82", ModelValue::make_integer(1).value}); // "あ"
    auto res_bmp = ModelValue::make_object(std::move(members_bmp));
    assert(res_bmp.error == ModelError::OK);
    auto ser_bmp = res_bmp.value.serialize();
    assert(ser_bmp.error == ModelError::OK);
    assert(ser_bmp.value == "{\"\xE3\x81\x82\":1,\"\xE3\x81\x84\":2}");

    // Surrogate-pair sensitive: U+2603 SNOWMAN vs U+1F600 GRINNING FACE
    ObjectValue members_surrogate;
    members_surrogate.push_back({"\xF0\x9F\x98\x80", ModelValue::make_integer(2).value}); // U+1F600
    members_surrogate.push_back({"\xE2\x98\x83", ModelValue::make_integer(1).value});     // U+2603
    auto res_surrogate = ModelValue::make_object(std::move(members_surrogate));
    assert(res_surrogate.error == ModelError::OK);
    auto ser_surrogate = res_surrogate.value.serialize();
    assert(ser_surrogate.error == ModelError::OK);
    assert(ser_surrogate.value == "{\"\xE2\x98\x83\":1,\"\xF0\x9F\x98\x80\":2}");

    // Mixed ASCII / non-ASCII
    ObjectValue members_mixed;
    members_mixed.push_back({"\xE2\x98\x83", ModelValue::make_integer(3).value}); // U+2603
    members_mixed.push_back({"a", ModelValue::make_integer(1).value});            // U+0061
    members_mixed.push_back({"\xC2\xA2", ModelValue::make_integer(2).value});     // U+00A2
    auto res_mixed = ModelValue::make_object(std::move(members_mixed));
    assert(res_mixed.error == ModelError::OK);
    auto ser_mixed = res_mixed.value.serialize();
    assert(ser_mixed.error == ModelError::OK);
    assert(ser_mixed.value == "{\"a\":1,\"\xC2\xA2\":2,\"\xE2\x98\x83\":3}");

    // No Unicode Normalization: Precomposed vs Decomposed
    ObjectValue members_norm;
    members_norm.push_back({"\xC3\xA9", ModelValue::make_integer(2).value});       // U+00E9
    members_norm.push_back({"e\xCC\x81", ModelValue::make_integer(1).value});      // U+0065 U+0301
    auto res_norm = ModelValue::make_object(std::move(members_norm));
    assert(res_norm.error == ModelError::OK);
    auto ser_norm = res_norm.value.serialize();
    assert(ser_norm.error == ModelError::OK);
    assert(ser_norm.value == "{\"e\xCC\x81\":1,\"\xC3\xA9\":2}");
}

void test_serialize_invalid_utf8() {
    ObjectValue members;
    members.push_back({"hello\xFFworld", ModelValue::make_integer(1).value});
    auto res = ModelValue::make_object(std::move(members));
    assert(res.error == ModelError::OK); // Init OK

    auto ser = res.value.serialize();
    assert(ser.error == ModelError::INVALID_ARG); // Serialize fails due to validation

    // Check another invalid format: overlong encoding
    ObjectValue members2;
    members2.push_back({"\xC0\xAF", ModelValue::make_integer(1).value});
    auto res2 = ModelValue::make_object(std::move(members2));
    auto ser2 = res2.value.serialize();
    assert(ser2.error == ModelError::INVALID_ARG);

    // Missing continuation byte
    ObjectValue members3;
    members3.push_back({"\xE2\x98", ModelValue::make_integer(1).value});
    auto res3 = ModelValue::make_object(std::move(members3));
    auto ser3 = res3.value.serialize();
    assert(ser3.error == ModelError::INVALID_ARG);

    // Invalid surrogate in UTF-8
    ObjectValue members4;
    members4.push_back({"\xED\xA0\x80", ModelValue::make_integer(1).value}); // D800
    auto res4 = ModelValue::make_object(std::move(members4));
    auto ser4 = res4.value.serialize();
    assert(ser4.error == ModelError::INVALID_ARG);

    // Above U+10FFFF
    ObjectValue members5;
    members5.push_back({"\xF4\x90\x80\x80", ModelValue::make_integer(1).value}); // U+110000
    auto res5 = ModelValue::make_object(std::move(members5));
    auto ser5 = res5.value.serialize();
    assert(ser5.error == ModelError::INVALID_ARG);
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

void test_serialize_repeated() {
    // Ensure output remains stable after repeated serialization calls
    auto res_normal = ModelValue::make_string("stable value");
    assert(res_normal.error == ModelError::OK);

    auto ser1 = res_normal.value.serialize();
    assert(ser1.error == ModelError::OK);

    auto ser2 = res_normal.value.serialize();
    assert(ser2.error == ModelError::OK);

    assert(ser1.value == ser2.value);
    assert(ser1.value == "\"stable value\"");
}

void test_serialize_large_array() {
    // Large but bounded array serialization to exercise string growth
    const size_t array_size = 2000;
    ArrayValue elements;
    elements.reserve(array_size);
    for (size_t i = 0; i < array_size; ++i) {
        elements.push_back(ModelValue::make_string("test_growth_element").value);
    }

    auto res_array = ModelValue::make_array(std::move(elements));
    assert(res_array.error == ModelError::OK);

    auto ser = res_array.value.serialize();
    assert(ser.error == ModelError::OK);

    assert(ser.value.front() == '[');
    assert(ser.value.back() == ']');
    // Check prefix
    assert(ser.value.substr(0, 23) == "[\"test_growth_element\",");
}


void test_serialize_control_characters() {
    auto res_short = ModelValue::make_string("backspace\b formfeed\f newline\n cr\r tab\t quote\" slash/");
    assert(res_short.error == ModelError::OK);
    auto ser_short = res_short.value.serialize();
    assert(ser_short.error == ModelError::OK);
    assert(ser_short.value == "\"backspace\\b formfeed\\f newline\\n cr\\r tab\\t quote\\\" slash/\"");

    auto res_other = ModelValue::make_string("ctrl\x01\x1F");
    assert(res_other.error == ModelError::OK);
    auto ser_other = res_other.value.serialize();
    assert(ser_other.error == ModelError::OK);
    assert(ser_other.value == "\"ctrl\\u0001\\u001f\"");
}

void test_serialize_empty_string_and_key() {
    auto res_empty_str = ModelValue::make_string("");
    assert(res_empty_str.error == ModelError::OK);
    auto ser_empty_str = res_empty_str.value.serialize();
    assert(ser_empty_str.error == ModelError::OK);
    assert(ser_empty_str.value == "\"\"");

    ObjectValue members;
    members.push_back({"", ModelValue::make_integer(1).value});
    auto res_empty_key = ModelValue::make_object(std::move(members));
    assert(res_empty_key.error == ModelError::OK);
    auto ser_empty_key = res_empty_key.value.serialize();
    assert(ser_empty_key.error == ModelError::OK);
    assert(ser_empty_key.value == "{\"\":1}");
}

void test_serialize_non_bmp() {
    auto res_non_bmp = ModelValue::make_string("😊");
    assert(res_non_bmp.error == ModelError::OK);
    auto ser_non_bmp = res_non_bmp.value.serialize();
    assert(ser_non_bmp.error == ModelError::OK);
    assert(ser_non_bmp.value == "\"\xF0\x9F\x98\x8A\"");

    auto res_bmp = ModelValue::make_string("äöü");
    assert(res_bmp.error == ModelError::OK);
    auto ser_bmp = res_bmp.value.serialize();
    assert(ser_bmp.error == ModelError::OK);
    assert(ser_bmp.value == "\"\xC3\xA4\xC3\xB6\xC3\xBC\"");
}

void test_serialize_deep_nesting() {
    ObjectValue obj_c;
    obj_c.push_back({"c", ModelValue::make_integer(1).value});

    ObjectValue obj_b;
    obj_b.push_back({"b", ModelValue::make_object(std::move(obj_c)).value});

    ObjectValue obj_a;
    obj_a.push_back({"a", ModelValue::make_object(std::move(obj_b)).value});

    auto res = ModelValue::make_object(std::move(obj_a));
    assert(res.error == ModelError::OK);
    auto ser = res.value.serialize();
    assert(ser.error == ModelError::OK);
    assert(ser.value == "{\"a\":{\"b\":{\"c\":1}}}");
}


void test_serialize_utf16_ordering() {
    ObjectValue members;
    members.push_back({"𐀀", ModelValue::make_integer(1).value});
    members.push_back({"嶲", ModelValue::make_integer(2).value});
    members.push_back({"a", ModelValue::make_integer(3).value});
    members.push_back({"é", ModelValue::make_integer(4).value});

    auto res = ModelValue::make_object(std::move(members));
    assert(res.error == ModelError::OK);
    auto ser = res.value.serialize();
    assert(ser.error == ModelError::OK);
    assert(ser.value == "{\"a\":3,\"é\":4,\"𐀀\":1,\"嶲\":2}" || ser.value == "{\"a\":3,\"\xC3\xA9\":4,\"\xF0\x90\x80\x80\":1,\"\xF0\xAF\xA7\xB4\":2}");
}

void test_serialize_safe_integer_boundaries() {
    auto res_max = ModelValue::make_integer(9007199254740991LL);
    assert(res_max.error == ModelError::OK);
    auto ser_max = res_max.value.serialize();
    assert(ser_max.error == ModelError::OK);
    assert(ser_max.value == "9007199254740991");

    auto res_min = ModelValue::make_integer(-9007199254740991LL);
    assert(res_min.error == ModelError::OK);
    auto ser_min = res_min.value.serialize();
    assert(ser_min.error == ModelError::OK);
    assert(ser_min.value == "-9007199254740991");
}

void test_serialize_backslash_escape() {
    auto res = ModelValue::make_string("back\\\\slash");
    assert(res.error == ModelError::OK);
    auto ser = res.value.serialize();
    assert(ser.error == ModelError::OK);
    assert(ser.value == "\"back\\\\\\\\slash\"");
}


void test_serialize_invalid_utf8_object_keys_more() {
    ObjectValue members;
    members.push_back({"\xFF", ModelValue::make_integer(1).value});
    auto res = ModelValue::make_object(std::move(members));
    assert(res.error == ModelError::OK);
    auto ser = res.value.serialize();
    assert(ser.error == ModelError::INVALID_ARG);

    auto res_str = ModelValue::make_string("\xFF");
    assert(res_str.error == ModelError::OK);
    auto ser_str = res_str.value.serialize();
    assert(ser_str.error == ModelError::OK);
    assert(ser_str.value == "\"\xFF\"");
}

int main() {
    test_serialize_invalid_utf8_object_keys_more();
    test_serialize_utf16_ordering();
    test_serialize_safe_integer_boundaries();
    test_serialize_backslash_escape();
    test_serialize_control_characters();
    test_serialize_empty_string_and_key();
    test_serialize_non_bmp();
    test_serialize_deep_nesting();
    std::cout << "Running C++ JCS model serializer tests..." << std::endl;
    test_serialize_null();
    test_serialize_boolean();
    test_serialize_integer();
    test_serialize_string();
    test_serialize_array();
    test_serialize_object_ordering();
    test_serialize_object_ordering_utf16();
    test_serialize_invalid_utf8();
    test_serialize_nested();
    test_serialize_repeated();
    test_serialize_large_array();
    std::cout << "C++ JCS model serializer tests passed." << std::endl;
    return 0;
}
