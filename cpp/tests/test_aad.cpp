#include <iostream>
#include <string>
#include <iomanip>
#include <sstream>
#include "vault_aad_internal.hpp"
#include "generated_aad_vectors.h"

std::string to_hex(const std::string& input) {
    std::ostringstream oss;
    for (unsigned char c : input) {
        oss << std::hex << std::setw(2) << std::setfill('0') << (int)c;
    }
    return oss.str();
}

int main() {
    int failures = 0;

    std::cout << "Running AAD vector tests...\n";

    for (int i = 0; i < NUM_AAD_TEST_VECTORS; ++i) {
        const AadTestVector& v = AAD_TEST_VECTORS[i];
        std::string actual_string;

        std::string policy = v.policy ? v.policy : "";
        if (policy == "record-payload-v1") {
            actual_string = vault::aad::record_payload_v1(v.object_uuid, v.schema_uuid, v.content_type, v.kid, v.alg);
        } else if (policy == "wrap-database-key-v1") {
            actual_string = vault::aad::wrap_database_key_v1(v.wrapped_kid, v.wrapping_kid);
        } else if (policy == "wrap-record-key-v1") {
            actual_string = vault::aad::wrap_record_key_v1(v.wrapped_kid, v.wrapping_kid);
        } else {
            std::cerr << "FAIL: Unknown policy '" << policy << "' for vector '" << v.name << "'\n";
            failures++;
            continue;
        }

        std::string expected_string = v.expected_string ? v.expected_string : "";
        if (actual_string != expected_string) {
            std::cerr << "FAIL: String mismatch for vector '" << v.name << "'\n"
                      << "  Expected: " << expected_string << "\n"
                      << "  Actual  : " << actual_string << "\n";
            failures++;
            continue;
        }

        std::string actual_hex = to_hex(actual_string);
        std::string expected_hex = v.expected_hex ? v.expected_hex : "";

        if (actual_hex != expected_hex) {
            std::cerr << "FAIL: Hex mismatch for vector '" << v.name << "'\n"
                      << "  Expected: " << expected_hex << "\n"
                      << "  Actual  : " << actual_hex << "\n";
            failures++;
        }
    }

    std::cout << "Running AAD escaping regression tests...\n";

    struct RegressionCase {
        std::string name;
        std::string policy;
        std::string obj_uuid;
        std::string sch_uuid;
        std::string ctype;
        std::string kid;
        std::string alg;
        std::string wrapped_kid;
        std::string wrapping_kid;
        std::string expected_str;
        std::string expected_hex;
    };

    RegressionCase regression_cases[] = {
        {
            "double-quote", "record-payload-v1",
            "u1", "s1", "application/example; note=\"x\"", "k1", "A256GCM", "", "",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"application/example; note=\\\"x\\\"\",\"kid\":\"k1\",\"object_uuid\":\"u1\",\"schema_uuid\":\"s1\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a226170706c69636174696f6e2f6578616d706c653b206e6f74653d5c22785c22222c226b6964223a226b31222c226f626a6563745f75756964223a227531222c22736368656d615f75756964223a227331222c2276223a317d"
        },
        {
            "backslash", "record-payload-v1",
            "u1", "s1", "domain\\user", "k1", "A256GCM", "", "",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"domain\\\\user\",\"kid\":\"k1\",\"object_uuid\":\"u1\",\"schema_uuid\":\"s1\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a22646f6d61696e5c5c75736572222c226b6964223a226b31222c226f626a6563745f75756964223a227531222c22736368656d615f75756964223a227331222c2276223a317d"
        },
        {
            "newline-tab", "record-payload-v1",
            "u1\n", "s1\t", "type", "k1", "A256GCM", "", "",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"type\",\"kid\":\"k1\",\"object_uuid\":\"u1\\n\",\"schema_uuid\":\"s1\\t\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a2274797065222c226b6964223a226b31222c226f626a6563745f75756964223a2275315c6e222c22736368656d615f75756964223a2273315c74222c2276223a317d"
        },
        {
            "control-char-01", "record-payload-v1",
            "u1", "s1", "t\x01y", "k1", "A256GCM", "", "",
            "{\"aad_policy\":\"record-payload-v1\",\"alg\":\"A256GCM\",\"content_type\":\"t\\u0001y\",\"kid\":\"k1\",\"object_uuid\":\"u1\",\"schema_uuid\":\"s1\",\"v\":1}",
            "7b226161645f706f6c696379223a227265636f72642d7061796c6f61642d7631222c22616c67223a224132353647434d222c22636f6e74656e745f74797065223a22745c753030303179222c226b6964223a226b31222c226f626a6563745f75756964223a227531222c22736368656d615f75756964223a227331222c2276223a317d"
        },
        {
            "wrap-db-key-escaping", "wrap-database-key-v1",
            "", "", "", "", "", "w\"k\n", "wr\x01k\\",
            "{\"aad_policy\":\"wrap-database-key-v1\",\"v\":1,\"wrapped_kid\":\"w\\\"k\\n\",\"wrapping_kid\":\"wr\\u0001k\\\\\"}",
            "7b226161645f706f6c696379223a22777261702d64617461626173652d6b65792d7631222c2276223a312c22777261707065645f6b6964223a22775c226b5c6e222c227772617070696e675f6b6964223a2277725c75303030316b5c5c227d"
        },
        {
            "wrap-record-key-escaping", "wrap-record-key-v1",
            "", "", "", "", "", "k1\t", "k2\"",
            "{\"aad_policy\":\"wrap-record-key-v1\",\"v\":1,\"wrapped_kid\":\"k1\\t\",\"wrapping_kid\":\"k2\\\"\"}",
            "7b226161645f706f6c696379223a22777261702d7265636f72642d6b65792d7631222c2276223a312c22777261707065645f6b6964223a226b315c74222c227772617070696e675f6b6964223a226b325c22227d"
        }
    };

    for (const auto& rc : regression_cases) {
        std::string actual_string;
        if (rc.policy == "record-payload-v1") {
            actual_string = vault::aad::record_payload_v1(rc.obj_uuid, rc.sch_uuid, rc.ctype, rc.kid, rc.alg);
        } else if (rc.policy == "wrap-database-key-v1") {
            actual_string = vault::aad::wrap_database_key_v1(rc.wrapped_kid, rc.wrapping_kid);
        } else if (rc.policy == "wrap-record-key-v1") {
            actual_string = vault::aad::wrap_record_key_v1(rc.wrapped_kid, rc.wrapping_kid);
        } else {
            std::cerr << "FAIL: Unknown policy '" << rc.policy << "' for regression '" << rc.name << "'\n";
            failures++;
            continue;
        }

        if (actual_string != rc.expected_str) {
            std::cerr << "FAIL: String mismatch for regression '" << rc.name << "'\n"
                      << "  Expected: " << rc.expected_str << "\n"
                      << "  Actual  : " << actual_string << "\n";
            failures++;
            continue;
        }

        std::string actual_hex = to_hex(actual_string);
        if (actual_hex != rc.expected_hex) {
            std::cerr << "FAIL: Hex mismatch for regression '" << rc.name << "'\n"
                      << "  Expected: " << rc.expected_hex << "\n"
                      << "  Actual  : " << actual_hex << "\n";
            failures++;
        }
    }

    if (failures == 0) {
        std::cout << "All AAD vector and regression tests passed.\n";
        return 0;
    } else {
        std::cerr << failures << " test(s) failed.\n";
        return 1;
    }
}
