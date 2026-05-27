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
| FINDING-005 | 2026-05-25 | Payload | Go/Rust | `test-vectors/payload/payload-encryption-v1.json` defines negative tests for AAD tampering by providing intentionally mismatched metadata (e.g. `object_uuid`) that differs from the AAD embedded in the `expected_aad_hex` and ciphertext. To validate decryption failure, implementations must use the explicitly provided mismatched metadata to reconstruct the AAD, which will then correctly fail AES-GCM authentication. | clarification | Low | Payload negative vectors may use mismatched metadata to cause reconstructed AAD to differ from the AAD used for the expected ciphertext. Go/Rust payload validation reconstructs AAD from the vector metadata and asserts AES-GCM decryption failure for invalid vectors. | Active | `test-vectors/payload/payload-encryption-v1.json`, `go/payload_test.go`, `rust/tests/payload_conformance.rs` |
| FINDING-006 | 2026-05-25 | SQLite | Go/Rust | `modernc.org/sqlite` in Go and `rusqlite` in Rust successfully read `PRAGMA application_id` and `PRAGMA user_version`. In both languages, we use `file:<path>?mode=ro` (or equivalent `SQLITE_OPEN_READ_ONLY | SQLITE_OPEN_URI` flags) to ensure strict read-only operation. No critical divergence observed for simple reads. | implementation-note | Low | File-backed Go/Rust implementations apply standard PRAGMA checks and do not use the browser `sql.js` exception. | Active | `go/internal/sqlitev1/validator.go`, `rust/src/sqlitev1.rs` |
| FINDING-007 | 2026-05-25 | SQLite | Go/Rust | `database_uuid` validation requires strict enforcement of the RFC4122/RFC9562-compatible variant layout (version 1-8, variant 8/9/a/b) rather than just allowing any canonical 8-4-4-4-12 hex shape. This prevents cross-language portability divergence by ensuring invalid versions and variants are rejected explicitly across all implementations. | clarification | Low | Ensured the strict regex pattern (`^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`) is used and explicitly documented in Rust and Go to validate UUID version and variant bits. | Active | `go/internal/sqlitev1/validator.go`, `rust/src/sqlitev1.rs` |

## FINDING-008: Strict "active" key status requirement for database_kek during unlock

- **Tag:** `clarification`
- **Area:** Storage Format / API Implementation
- **Description:** During the implementation of the read-only unlock/decrypt reader in Go and Rust, the reader must find a `database_kek` to unwrap. The current implementation strictly enforces `status = 'active'` during the query. While `decrypt_only` might be logically sound for a read-only compatibility scenario (e.g., during key rotation or migrations), it is currently not permitted.
- **Impact:** `decrypt_only`, `disabled`, and `destroyed` states are unsupported for the initial database unlock operation, causing a failure to find an active key. This matches the current Python baseline.
- **Resolution:** No immediate changes to the schema or current code. The Go and Rust reader implementations explicitly require `status = 'active'`. The semantics and test coverage for `decrypt_only` require further clarification before being implemented.

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

## FINDING-009: Strict UUID enforcement in Writers
- **Tag:** `implementation-note`
- **Area:** Storage Format / API Implementation
- **Description:** When inserting new rows containing `schema_uuid` or generating `object_uuid`, writers must proactively validate or generate strict RFC4122/RFC9562-compatible UUIDs (`^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`). While standard V4 generator libraries in Go and Rust produce valid compliant UUIDs, inputs like `schema_uuid` must be explicitly verified to prevent silent database corruption from non-compliant caller arguments.
- **Impact:** Low. Added strict regex validation in Go and Rust writer scaffolds.
- **Resolution:** Validated and enforced inside `store_payload`.

## FINDING-010: Explicit Transactions in Writers
- **Tag:** `implementation-note`
- **Area:** Storage Format / API Implementation
- **Description:** The `PRAGMA foreign_keys = ON` constraint must be explicitly set *before* opening an initialization or insertion transaction in Go and Rust SQLite drivers. Both scaffolds were hardened to perform all metadata and payload writes atomically, rolling back safely if any step (such as cryptography or UUID generation) fails.
- **Impact:** High for robustness.
- **Resolution:** Explicit `BEGIN` and `COMMIT` block management in Go and Rust was confirmed and hardened.
