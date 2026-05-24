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
| `storage_metadata_tbl` is required and validated | Satisfied | [`schema.sql`](../backend/sqlite/schema.sql), [`test_metadata.py`](../../python/tests/test_metadata.py), [`metadata.test.js`](../../nodejs/test/metadata.test.js) | No |
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

## 4. Criteria Already Satisfied

All core stabilization criteria outlined in the table above have been satisfied. The V1 format semantics and exact physical storage profile definitions are stable. The implementation matrix effectively tests and verifies compliance via static cryptographic primitives and dynamic semantic interoperability testing.

## 5. Documented Exceptions

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

Prior to declaring Storage Format V1 formally Stable, the following final review checklist must be verified:

- [ ] Latest CI runs are green.
- [ ] Codecov upload is working and README badge renders.
- [ ] No stale “Draft only / pending coverage / not CI integrated” wording remains in core docs.
- [ ] [`implementation-gaps.md`](../implementation-notes/implementation-gaps.md) still reports no V1-blocking storage-format gaps.
- [ ] Future work remains clearly non-blocking.
- [ ] No implementation, schema, test vector, or workflow YAML changes were made during this final evidence-hardening step.

## 8. Decision Summary

Based on this readiness review, Storage Format V1 has met all stability criteria across multiple implementations (Python, Node.js, and browser-test). The cross-language compatibility guarantees are solid, backed by comprehensive testing and CI workflows. The remaining work is correctly scoped as non-blocking enhancements or language ports that do not require changes to the fundamental V1 storage format.

The format is a stable candidate and is ready for final review leading up to a formal stable declaration.
