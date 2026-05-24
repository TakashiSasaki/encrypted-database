# Storage Format V1 Readiness Review

## 1. Purpose

The purpose of this document is to evaluate the current readiness of the Encrypted Database Storage Format V1 to be declared "Stable." It outlines the criteria for stabilization, the status of current implementations across different environments (Python, Node.js, browser-test), documented exceptions, and non-blocking future work.

This is a readiness review document and does not serve as the formal Stable declaration itself. Instead, it provides the required context and justification for why the V1 format is a stable candidate.

## 2. Current Status

**Status:** Ready for final review / Stable candidate
**V1-blocking storage-format gaps:** None known.

Implementations for Python, Node.js, and browser-test have been successfully implemented, and cross-language equivalence is guaranteed by a comprehensive test suite of cryptographic primitives and roundtrip integration tests.

## 3. Stable Declaration Criteria and Status

To declare the V1 format stable, all required components must be fully specified, correctly implemented, and validated.

| Criteria | Status | Evidence | Blocking? |
| :--- | :--- | :--- | :--- |
| Format identity is fixed | Satisfied | [`storage-format.md`](./storage-format.md) | No |
| SQLite profile identity is fixed | Satisfied | [`storage-format-sqlite.md`](./storage-format-sqlite.md) | No |
| `storage_metadata_tbl` is required and validated | Satisfied | [`schema.sql`](../backend/sqlite/schema.sql), backend validation | No |
| `PRAGMA application_id` / `user_version` policy is defined | Satisfied | [`storage-format-sqlite.md`](./storage-format-sqlite.md) | No |
| browser/sql.js PRAGMA exception is documented | Documented Exception | [`storage-format-sqlite.md`](./storage-format-sqlite.md) | No |
| Required/optional feature handling is defined | Satisfied | [`storage-format.md`](./storage-format.md) | No |
| Unknown features are rejected in V1 | Satisfied | [`storage-format.md`](./storage-format.md) | No |
| JCS canonicality policy is defined and tested | Satisfied | [`terminology.md`](./terminology.md), [`test-vectors.md`](./test-vectors.md) | No |
| `provider_config_json` is explicit and validated | Satisfied | [`api-contract.md`](./api-contract.md) | No |
| Argon2id Profile V1 parameters are fixed | Satisfied | [`test-vectors.md`](./test-vectors.md), [`providers/passphrase-argon2id.md`](../providers/passphrase-argon2id.md) | No |
| AAD policy is fixed | Satisfied | [`aad-policy.md`](./aad-policy.md) | No |
| Ciphertext format is fixed | Satisfied | [`envelope-format.md`](./envelope-format.md) | No |
| Payload canonicalization and raw-buffer rejection are implemented | Satisfied | [`api-contract.md`](./api-contract.md) | No |
| Python / Node.js / browser-test test vectors pass | Satisfied | CI runs, [`test-vectors.md`](./test-vectors.md) | No |
| Python ↔ Node.js roundtrip is CI integrated | Satisfied | CI runs, `integration-tests/roundtrip` | No |
| Coverage and CI visibility exist | Satisfied | CI runs, README badges | No |
| V1-blocking storage-format gaps are none | Satisfied | [`implementation-gaps.md`](../implementation-notes/implementation-gaps.md) | No |

## 4. Criteria Already Satisfied

All core stabilization criteria outlined in the table above have been satisfied. The V1 format semantics and exact physical storage profile definitions are stable. The implementation matrix effectively tests and verifies compliance via static cryptographic primitives and dynamic semantic interoperability testing.

## 5. Documented Exceptions

While V1 stabilization expects strict conformance, the following intentional exceptions have been documented and accepted for specific environments:

- **Browser-test / sql.js file-header PRAGMAs**: `sql.js` does not validate SQLite file-header PRAGMAs. This exception is officially documented.
- **Browser-test / sql.js corruption testing**: `browser-test / sql.js` does not require malformed-on-disk corruption testing via `PRAGMA ignore_check_constraints`.
- **Browser-test coverage context**: Browser-test coverage is Jest JSDOM/sql.js harness coverage, not real browser runtime (WebCrypto) coverage.

## 6. Non-Blocking Future Work

The following items are recognized as important future enhancements or active work items but are explicitly classified as **non-blocking** for declaring Storage Format V1 stable. See [`implementation-gaps.md`](../implementation-notes/implementation-gaps.md) for more details.

- Go implementation
- Rust implementation
- Go/Rust roundtrip integration tests
- Browser export/import roundtrip testing
- Browser real-runtime (WebCrypto) coverage
- Dynamic `created_by_version` discovery
- Schema fingerprint / hash (DDL integrity)
- Optional feature read-only fallback
- Safe integer policy
- Key rotation
- Additional unlock providers
- Blind index searchability
- Packaging/distribution maturity

## 7. Remaining Stabilization Items

At this time, there are **no known blocking items** preventing a stable declaration. All necessary criteria have been verified, and the core documents correctly align with implementation status.

## 8. Decision Summary

Based on this readiness review, Storage Format V1 has met all stability criteria across multiple implementations (Python, Node.js, and browser-test). The cross-language compatibility guarantees are solid, backed by comprehensive testing and CI workflows. The remaining work is correctly scoped as non-blocking enhancements or language ports that do not require changes to the fundamental V1 storage format.

The format is a stable candidate and is ready for final review leading up to a formal stable declaration.
