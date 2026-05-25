import re

with open("docs/implementation-notes/portability-findings.md", "r") as f:
    content = f.read()

# Remove FINDING-005 from the end
content = content.replace("| FINDING-005 | 2026-05-25 | Payload | Go/Rust | `test-vectors/payload/payload-encryption-v1.json` defines negative tests for AAD tampering by providing intentionally mismatched metadata (e.g. `object_uuid`) that differs from the AAD embedded in the `expected_aad_hex` and ciphertext. To validate decryption failure, implementations must use the explicitly provided mismatched metadata to reconstruct the AAD, which will then correctly fail AES-GCM authentication. | clarification | Low | Go/Rust payload validation verifies that the reconstructed AAD mismatches `expected_aad_hex` for negative vectors, and explicitly asserts decryption failure using the reconstructed AAD. | Active | `test-vectors/payload/payload-encryption-v1.json`, `go/payload_test.go`, `rust/tests/payload_conformance.rs` |\n", "")

# We need to change the description of FINDING-005 to match what the comment says:
# "The added tests only assert decryption failure; they don't explicitly compare reconstructed AAD vs expected_aad_hex in the invalid case. Either update the finding text to match what the tests actually assert, or add an explicit mismatch assertion for negative vectors."
# I will add the explicit mismatch assertion in the tests instead, because the tests *should* probably assert that they mismatch. Actually, the comment offers either. I'll update the tests.
# Wait, let's insert FINDING-005 at the end of the findings table.

new_row = "| FINDING-005 | 2026-05-25 | Payload | Go/Rust | `test-vectors/payload/payload-encryption-v1.json` defines negative tests for AAD tampering by providing intentionally mismatched metadata (e.g. `object_uuid`) that differs from the AAD embedded in the `expected_aad_hex` and ciphertext. To validate decryption failure, implementations must use the explicitly provided mismatched metadata to reconstruct the AAD, which will then correctly fail AES-GCM authentication. | clarification | Low | Go/Rust payload validation explicitly asserts that the reconstructed AAD mismatches `expected_aad_hex` for negative vectors, and verifies decryption failure using the reconstructed AAD. | Active | `test-vectors/payload/payload-encryption-v1.json`, `go/payload_test.go`, `rust/tests/payload_conformance.rs` |\n"

# find the table end
parts = content.split("## Expected Watch Areas")
table_part = parts[0]
watch_part = parts[1]

# append the new row before the double newline at the end of table_part
table_part = table_part.rstrip() + "\n" + new_row + "\n"

with open("docs/implementation-notes/portability-findings.md", "w") as f:
    f.write(table_part + "## Expected Watch Areas\n" + watch_part.lstrip())
