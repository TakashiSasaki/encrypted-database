# Portability Findings Log

This log tracks issues discovered during the Go and Rust portability validation phase.
Go/Rust portability validation is performed relative to the `tag-1.z.z` Storage Format V1 stable baseline.

## Findings

| ID | Date | Area | Observed in | Issue | Classification | Impact | Decision | Status | Related files/tests |
|---|---|---|---|---|---|---|---|---|---|
| FINDING-001 | 2026-05-25 | JCS | Go/Rust | Go `encoding/json` and Rust `serde_json` standard marshalling do not strictly conform to RFC 8785 (JCS) regarding float formatting and map key ordering without explicit `BTreeMap` or custom sorting implementations. | driver-or-library-limitation | Moderate | Developed minimal custom JCS canonicalizer targeting basic JSON shapes for AAD/JCS vectors. Full JCS support may require finding reliable 3rd-party libs or completing the custom implementations. | Active | `go/internal/jcs`, `rust/src/jcs.rs` |
| FINDING-002 | 2026-05-25 | KDF | Go/Rust | KDF primitive vectors currently use `salt_hex`, while `provider_config_json` uses `base64url` salt without padding. This is acceptable for primitive KDF conformance testing, but future provider_config conformance tests should cover strict base64url without padding. | clarification | Low | Go and Rust implementations now have strict base64url helpers ready for provider_config validation, but process `salt_hex` primarily for KDF primitives. | Active | `test-vectors/kdf/argon2id-v1.json`, `go/kdf_test.go`, `rust/tests/kdf_conformance.rs` |

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
| FINDING-003 | 2026-05-25 | AEAD | Go/Rust | AES-256-GCM APIs in Go (`cipher.AEAD.Seal`) and Rust (`aes-gcm` crate) return the ciphertext and authentication tag concatenated as `ciphertext || tag`. This implicitly aligns with the storage format, but it requires parsing to compare directly with separated test vector fields, if they are separated. | implementation-note | Low | No changes needed in implementations, but test vectors should consistently expect or represent the concatenated format when necessary. | Active | `go/aead_test.go`, `rust/tests/aead_conformance.rs` |
