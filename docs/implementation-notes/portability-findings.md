# Portability Findings Log

This log tracks issues discovered during the Go and Rust portability validation phase.
Go/Rust portability validation is performed relative to the `tag-1.z.z` Storage Format V1 stable baseline.

## Findings

| ID | Date | Area | Observed in | Issue | Classification | Impact | Decision | Status | Related files/tests |
|---|---|---|---|---|---|---|---|---|---|
| FINDING-001 | 2026-05-25 | JCS | Go/Rust | Go `encoding/json` and Rust `serde_json` standard marshalling do not strictly conform to RFC 8785 (JCS) regarding float formatting and map key ordering without explicit `BTreeMap` or custom sorting implementations. | driver-or-library-limitation | Moderate | Developed minimal custom JCS canonicalizer targeting basic JSON shapes for AAD/JCS vectors. Full JCS support may require finding reliable 3rd-party libs or completing the custom implementations. | Active | `go/internal/jcs`, `rust/src/jcs.rs` |
| FINDING-002 | 2026-05-25 | KDF | Go/Rust | KDF primitive vectors currently use `salt_hex`, while `provider_config_json` uses `base64url` salt without padding. This is acceptable for primitive KDF conformance testing, but future provider_config conformance tests should cover strict base64url without padding. | clarification | Low | Go and Rust implementations now have strict base64url helpers ready for provider_config validation, but process `salt_hex` primarily for KDF primitives. | Active | `test-vectors/kdf/argon2id-v1.json`, `go/kdf_test.go`, `rust/tests/kdf_conformance.rs` |
| FINDING-003 | 2026-05-25 | AEAD | Go/Rust | AES-256-GCM APIs in Go (`cipher.AEAD.Seal`) and Rust (`aes-gcm` crate) return the ciphertext and authentication tag concatenated as `ciphertext || tag`. This implicitly aligns with the storage format, but it requires parsing to compare directly with separated test vector fields, if they are separated. | implementation-note | Low | No changes needed in implementations, but test vectors should consistently expect or represent the concatenated format when necessary. | Active | `go/aead_test.go`, `rust/tests/aead_conformance.rs` |
| FINDING-004 | 2026-05-25 | Key-Wrap | Go/Rust | `test-vectors/key-wrap/key-wrap-v1.json` provides AAD explicitly via `expected_aad_hex` and reconstruction fields (`aad_policy`, `wrapped_kid`, `wrapping_kid`). We reconstruct AAD using the policy fields and verify it matches the explicit `expected_aad_hex`. It's slightly ambiguous which is authoritative if they differ, but we expect both to match. | clarification | Low | Go/Rust key-wrap validation tests will verify both the reconstructed AAD and compare against `expected_aad_hex`. No vector changes required. | Active | `test-vectors/key-wrap/key-wrap-v1.json`, `go/key_wrap_test.go`, `rust/tests/key_wrap_conformance.rs` |
| FINDING-005 | 2026-05-25 | Payload | Go/Rust | `test-vectors/payload/payload-encryption-v1.json` defines negative tests for AAD tampering by providing intentionally mismatched metadata (e.g. `object_uuid`) that differs from the AAD embedded in the `expected_aad_hex` and ciphertext. To validate decryption failure, implementations must use the explicitly provided mismatched metadata to reconstruct the AAD, which will then correctly fail AES-GCM authentication. | clarification | Low | Go/Rust payload validation explicitly asserts that the reconstructed AAD mismatches `expected_aad_hex` for negative vectors, and verifies decryption failure using the reconstructed AAD. | Active | `test-vectors/payload/payload-encryption-v1.json`, `go/payload_test.go`, `rust/tests/payload_conformance.rs` |

## Expected Watch Areas
The following areas are anticipated points of divergence and should be monitored closely during the Go and Rust implementations:

- JCS canonicalization differences
- JSON number / safe integer handling
- UTF-8 and string normalization
- Base64url padding and alphabet strictness
- SQLite BLOB vs TEXT handling
- SQLite PRAGMA persistence
- SQLite foreign key activation
- SQLite driver transaction semantics
- UUID canonical validation
- Argon2id parameter mapping
- AES-GCM nonce/tag/ciphertext layout
- error taxonomy mapping
- sync vs async lifecycle differences
- file locking / close semantics
- content_type / MIME validation
- browser/sql.js exception boundaries
