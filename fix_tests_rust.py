import re

# Update rust/tests/payload_conformance.rs
with open("rust/tests/payload_conformance.rs", "r") as f:
    rust_content = f.read()

rust_mismatch_code = """
            if valid {
                assert_eq!(reconstructed_aad, expected_aad, "test '{}': reconstructed AAD does not match expected_aad_hex", name);
            } else {
                assert_ne!(reconstructed_aad, expected_aad, "test '{}': expected reconstructed AAD to mismatch expected_aad_hex for negative vector, but they matched", name);
            }
"""

rust_content = re.sub(
    r'if valid {\n\s*assert_eq!\(reconstructed_aad, expected_aad, "test \'{}\': reconstructed AAD does not match expected_aad_hex", name\);\n\s*}',
    rust_mismatch_code.strip(),
    rust_content
)

with open("rust/tests/payload_conformance.rs", "w") as f:
    f.write(rust_content)
