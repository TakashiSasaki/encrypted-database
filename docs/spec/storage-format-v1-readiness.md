# Storage Format V1 Stable Declaration Review

## 1. Purpose

The purpose of this document is to serve as the foundation and justification for declaring the Encrypted Database Storage Format V1 as "Stable." It outlines the criteria for stabilization, the status of current implementations across different environments (Python, Node.js, browser-test), documented exceptions, and non-blocking future work.

This document serves as the formal Stable declaration review for the V1 format. It clarifies that the stable status applies strictly to the Storage Format V1 and does not represent a production readiness declaration for the entire library.

## 2. Current Status

**Status:** Stable
**V1-blocking storage-format gaps:** None known.

Implementations for Python, Node.js, and browser-test have been successfully implemented, and cross-language equivalence is guaranteed by a comprehensive test suite of cryptographic primitives and roundtrip integration tests.

## 3. Stable Declaration Scope

The Stable declaration applies **strictly to the Storage Format V1**.

**Included in the Stable Scope:**
- Format identity
- SQLite storage profile identity
- `storage_metadata_tbl`
- Version / feature handling
- JCS canonicality requirements
- `provider_config_json` explicitness
- Argon2id Profile V1 parameters
- AAD policy
- Ciphertext / envelope format
- Payload canonicalization requirements
- SQLite CHECK constraints relevant to V1 invariants
- Python / Node.js / browser-test conformance expectations

**Excluded from the Stable Scope (Future Work/Not Stable Blockers):**
- Library production readiness
- Packaging/distribution maturity
- Go / Rust implementations
- Browser real-runtime coverage
- Browser export/import roundtrip
- Key rotation public APIs
- Additional unlock providers
- Blind index implementation
- Optional feature read-only fallback
- Schema fingerprint / hash
- Safe integer policy

## 4. Stable Declaration Criteria and Status

To declare the V1 format stable, all required components must be fully specified, correctly implemented, and validated.

| Criteria | Status | Evidence | Blocking? |
| :--- | :--- | :--- | :--- |
| Format identity is fixed | Satisfied | [`storage-format.md`](./storage-format.md) | No |
| SQLite profile identity is fixed | Satisfied | [`storage-format-sqlite.md`](./storage-format-sqlite.md) | No |
| `storage_metadata_tbl` is required and validated (including strict UUID policy) | Satisfied | [`schema.sql`](../backend/sqlite/schema.sql), [`test_metadata.py`](../../python/tests/test_metadata.py), [`metadata.test.js`](../../nodejs/test/metadata.test.js) | No |
| PRAGMA policy is defined and tested for Python / Node.js | Satisfied | [`storage-format-sqlite.md`](./storage-format-sqlite.md), [`test_metadata.py`](../../python/tests/test_metadata.py), [`metadata.test.js`](../../nodejs/test/metadata.test.js) | No |
| browser/sql.js PRAGMA exception is documented and tested | Documented Exception | [`storage-format-sqlite.md`](./storage-format-sqlite.md), [`v1_metadata_pragma.test.js`](../../browser-test/test/v1_metadata_pragma.test.js) | No |
| Required/optional feature handling is defined | Satisfied | [`storage-format.md`](./storage-format.md) | No |
| Unknown features are rejected in V1 | Satisfied | [`storage-format.md`](./storage-format.md) | No |
| JCS canonicality policy is defined and tested | Satisfied | [`terminology.md`](./terminology.md), [`test-vectors.md`](./test-vectors.md) | No |
| `provider_config_json` is explicit, JCS canonical, and strictly validated | Satisfied | [`api-contract.md`](./api-contract.md) | No |
| Argon2id Profile V1 parameters are fixed | Satisfied | [`test-vectors.md`](./test-vectors.md), [`passphrase-argon2id.md`](../providers/passphrase-argon2id.md) | No |
| AAD policy is fixed | Satisfied | [`aad-policy.md`](./aad-policy.md) | No |
| Ciphertext format is fixed | Satisfied | [`envelope-format.md`](./envelope-format.md) | No |
| Payload canonicalization and raw-buffer rejection are implemented | Satisfied | [`api-contract.md`](./api-contract.md) | No |
| Direct SQL CHECK constraints are implemented and tested for Python / Node.js | Satisfied | [`test_constraints.py`](../../python/tests/test_constraints.py), [`constraints.test.js`](../../nodejs/test/constraints.test.js) | No |
| browser-test has representative sql.js constraint coverage and documented file-backed exceptions | Satisfied | [`storage-format-sqlite.md`](./storage-format-sqlite.md) | No |
| Python / Node.js / browser-test test vectors pass | Satisfied | [`test-python.yml`](../../.github/workflows/test-python.yml), [`test-nodejs.yml`](../../.github/workflows/test-nodejs.yml), [`test-browser.yml`](../../.github/workflows/test-browser.yml), [`test-vectors.md`](./test-vectors.md) | No |
| Python ↔ Node.js roundtrip is CI integrated | Satisfied | [`test_roundtrip.sh`](../../integration-tests/roundtrip/test_roundtrip.sh), [`test-integration.yml`](../../.github/workflows/test-integration.yml) | No |
| Coverage and CI visibility exist | Satisfied | [`README.md`](../../README.md) | No |
| V1-blocking storage-format gaps are none | Satisfied | [`implementation-gaps.md`](../implementation-notes/implementation-gaps.md) | No |

## 5. Criteria Already Satisfied

All core stabilization criteria outlined in the table above have been satisfied. The V1 format semantics and exact physical storage profile definitions are stable. The implementation matrix effectively tests and verifies compliance via static cryptographic primitives and dynamic semantic interoperability testing.

## 6. Documented Exceptions

While V1 stabilization expects strict conformance, the following intentional exceptions have been documented and accepted for specific environments:

- **Browser-test / sql.js file-header PRAGMA validation exception**:
  - **Exception:** `sql.js` in the browser-test environment bypasses `PRAGMA application_id` and `PRAGMA user_version` validations.
  - **Reason:** `sql.js` operates purely in memory for this application layer, rendering standard file-backed SQLite header verification incompatible or unreliable.
  - **Coverage:** This is explicitly tested and documented as an exception in [`v1_metadata_pragma.test.js`](../../browser-test/test/v1_metadata_pragma.test.js) and [`storage-format-sqlite.md`](./storage-format-sqlite.md).
  - **Not a blocker:** The `storage_metadata_tbl` remains fully enforced as the primary identity source for the format. File-header metadata applies to the physical SQLite database file, which isn't standardly persisted or imported directly in the current browser architecture.

- **Browser-test / sql.js malformed-on-disk corruption testing exception**:
  - **Exception:** The `browser-test` environment skips direct SQL schema corruption tests using `PRAGMA ignore_check_constraints`.
  - **Reason:** Testing malformed data directly on-disk via this PRAGMA is not supported by the strict `sql.js` constraints (`CHECK(json_valid(...))`).
  - **Coverage:** Documented in [`implementation-gaps.md`](../implementation-notes/implementation-gaps.md).
  - **Not a blocker:** The validation policy and structural parity (API-layer validations and core semantics) are universally tested across all environments. The on-disk corruption tests are comprehensively handled by the Node.js and Python implementations.

- **Browser-test coverage context**:
  - **Exception:** Coverage reported for `browser-test` is generated from the Jest JSDOM/sql.js harness, not a real browser WebCrypto runtime.
  - **Reason:** Setting up real browser runtime coverage (via Playwright or Puppeteer) is complex and not fully implemented yet.
  - **Coverage:** Documented in [`README.md`](../../README.md) and [`implementation-gaps.md`](../implementation-notes/implementation-gaps.md).
  - **Not a blocker:** The `browser-test` harness achieves high logical coverage of the application and storage format logic. Real browser runtime paths are considered a future enhancement for operational confidence rather than a V1 format defect.

## 7. Non-Blocking Future Work

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

## 8. Post-Declaration Monitoring

At this time, there are **no known blocking items** preventing a stable declaration. All necessary criteria have been verified, and the core documents correctly align with implementation status.

The following items were verified as part of the formal Stable declaration review and will continue to be monitored:

- [x] Latest CI runs are green.
- [x] Codecov upload is working and README badge renders.
- [x] No stale “Draft only / pending coverage / not CI integrated” wording remains in core docs.
- [x] [`implementation-gaps.md`](../implementation-notes/implementation-gaps.md) still reports no V1-blocking storage-format gaps.
- [x] Future work remains clearly non-blocking.

## 9. Decision Summary

Based on this declaration review, Storage Format V1 has met all stability criteria across multiple implementations (Python, Node.js, and browser-test). The cross-language compatibility guarantees are solid, backed by comprehensive testing and CI workflows. The remaining work is correctly scoped as non-blocking enhancements or language ports that do not require changes to the fundamental V1 storage format.

Storage Format V1 is Declared Stable as of this review.
