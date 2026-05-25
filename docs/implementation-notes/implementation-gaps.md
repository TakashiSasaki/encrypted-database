# Implementation Gaps

This document tracks known discrepancies and gaps between the current specifications/decisions and the existing codebase.

## Active Gaps (V1-Blocking Storage-Format Gaps)

None.

*See [`../spec/storage-format-v1-readiness.md`](../spec/storage-format-v1-readiness.md) for the Storage Format V1 Stable Declaration Review and the rationale for treating known remaining work as non-blocking for the storage format.*

## Active Gaps (Future Hardening)

### Dynamic `created_by_version` discovery

**Status:** Future enhancement
**Area:** Deployment / Metadata
**Current state:** The `created_by_version` in the metadata table is hardcoded to `"0.0.0-dev"`. Dynamic discovery from package metadata (e.g. `package.json` or `pyproject.toml`) is not implemented.
**Expected or intended state:** The library dynamically discovers its own version at runtime or build time to embed in new databases.
**Why it matters:** Accurate version tracking helps diagnose issues with specific library versions.
**Recommended next action:** Implement dynamic version discovery as a packaging/metadata polish step.

### Schema fingerprint / hash

**Status:** Future enhancement
**Area:** Security
**Current state:** A canonical SQL `schema_hash` to guarantee exact DDL integrity is not implemented.
**Expected or intended state:** Implementations can compute and verify a hash of the current database schema.
**Why it matters:** Defends against subtle tampering of the underlying DDL.
**Recommended next action:** Defer until post-v1.

### Optional feature read-only fallback

**Status:** Future enhancement
**Area:** Usability
**Current state:** The V1 policy strictly rejects any unknown feature, including unknown optional features.
**Expected or intended state:** Implementations fall back to a strictly read-only mode to prevent overwriting or deleting data reliant on optional features without fully rejecting the open operation.
**Why it matters:** Enhances user experience when accessing a slightly newer vault with an older reader.
**Recommended next action:** Defer until post-v1.

### Safe integer policy

**Status:** Future enhancement
**Area:** Interoperability
**Current state:** A strict numeric portability policy across languages (Python arbitrary precision vs JavaScript IEEE 754 floats vs Go/Rust strict types) for payloads is not yet defined.
**Expected or intended state:** A documented constraint or schema validation protecting against precision loss.
**Why it matters:** Large numbers stored by Python could be silently truncated when read by JavaScript.
**Recommended next action:** Defer until post-v1 or resolve through documentation.

## Active Gaps (General)

### Go/Rust full storage libraries are not yet implemented

**Status:** Active
**Area:** Implementation
**Current state:** Go/Rust portability validation is active and materially implemented. The Go/Rust directories now include shared-vector conformance validation for JCS, AAD, Argon2id KDF, AES-256-GCM AEAD primitives, key-wrap, and payload encryption. They also include SQLite V1 read-only metadata validators that check PRAGMA markers and `storage_metadata_tbl` logical identity, including strict `database_uuid` validation.
**Expected or intended state:** Native Go and Rust packages expose full storage-library functionality, including database unlock/decrypt reader, writer APIs, lifecycle/key management operations, and cross-language roundtrip interoperability.
**Why it matters:** The storage format core is designed for multi-language support. Proving it in stricter compiled languages (Go/Rust) provides strong confidence.
**Recommended next action:** Implement Go/Rust database unlock/decrypt readers next, then add Go/Rust roundtrip matrix coverage before writer APIs.

### Roundtrip matrix does not yet include Go/Rust

**Status:** Active
**Area:** Interoperability
**Current state:** Semantic SQLite roundtrip tests exist between Python and Node.js. Go/Rust now have substantial portability-validation coverage and SQLite V1 read-only metadata validators, but they do not yet implement unlock/decrypt readers or writers and therefore are not yet part of the roundtrip matrix.
**Expected or intended state:** The roundtrip test matrix tests database creation, unlocking, reading, and writing across all supported languages (Python, Node.js, Go, Rust) and browser exports.
**Why it matters:** To guarantee true V1 interoperability.
**Recommended next action:** Expand the `test_roundtrip.sh` harness once Go/Rust full library read/write implementations are viable.

### JWE/JOSE compatibility is not implemented

**Status:** Active
**Area:** Standards Compatibility
**Current state:** The envelope format defined in `docs/spec/envelope-format.md` is custom and AEAD-oriented. It resembles JOSE/JWE concepts but is not a valid JWE serialization.
**Expected or intended state:** Documented clarity that JWE compatibility is not natively supported, but potentially provided via an export/adapter pattern.
**Why it matters:** Developers might incorrectly assume the library produces standard JWE tokens, leading to integration issues with external systems.
**Recommended next action:** Update documentation to clarify the non-JWE nature of the envelopes, and treat standard JWE export as a future enhancement rather than a current feature.

### Key rotation and lifecycle operations are not implemented

**Status:** Active
**Area:** Key Management
**Current state:** The schema supports `status`, activation/deactivation timestamps, and key classes, but public operations for key rotation, decrypt-only migration, destruction semantics, and rewrapping are not implemented.
**Expected or intended state:** Public APIs allowing consumers to securely rotate keys, rewrap data, and manage key lifecycles according to the schema capabilities.
**Why it matters:** Lack of key rotation makes the library unsuitable for long-term production use where cryptographic hygiene and rotation are mandated.
**Recommended next action:** Specify and implement key rotation, migration, and key destruction procedures.

### Additional unlock providers are schema/planned only

**Status:** Active
**Area:** Features
**Current state:** The schema lists multiple unlock methods and provider concepts, but only the passphrase (Argon2id) provider is currently implemented.
**Expected or intended state:** Implementation of, or clear documentation that other providers (OS secret store, hardware token, remote KMS, Shamir/threshold recovery) are strictly planned future features.
**Why it matters:** Users may be confused by schema references to features that are entirely non-functional in the library.
**Recommended next action:** Clearly document these as planned features or stub them out in the API contract.

### Blind index implementation is not complete

**Status:** Active
**Area:** Features
**Current state:** `docs/spec/blind-index.md` outlines HMAC-based blind indexes, but no corresponding API, tables, or tests exist in the current implementations.
**Expected or intended state:** A functional blind index API allowing searchable encrypted data.
**Why it matters:** Without blind indexes, the database cannot easily be queried based on payload contents, severely limiting its utility as a database.
**Recommended next action:** Implement the schema tables and API methods for blind indexes according to the specification.

### Input validation and canonicalization boundaries need hardening

**Status:** Partially Resolved
**Area:** Security / Input Validation
**Current state:** UUID formats, content types, and payloads are strictly validated at the public API boundary. Deep payload type checking is fully implemented, recursively rejecting raw buffers, typed arrays, and non-JSON values prior to canonicalization across Python, Node.js, and browser environments. Passphrase type invalidity is uniformly validated with a dedicated `InvalidPassphrase` error across all environments. The `StorageClosed` error correctly takes precedence over input validation errors on closed resources. Stricter MIME type parsing, full JSON Schema semantic validation, UUID registry semantic validation, and UI-level feedback in the browser demo remain future work.
**Expected or intended state:** Strict input validation and normalization at the public API boundary before interacting with the database.
**Why it matters:** Relying solely on database constraints can lead to unhandled database errors bubbling up instead of providing clear, early validation errors to the caller.
**Recommended next action:** Implement stricter MIME type parsing, and evaluate whether JSON Schema and UUID registry validations are within scope or out of scope.

### Packaging and distribution maturity is incomplete

**Status:** Active
**Area:** Deployment
**Current state:** Python and Node.js packaging metadata, exports, versioning, and setup scripts are present but lack the polish required for production publishing (e.g., missing comprehensive exports, mismatched versions, and incomplete README examples).
**Expected or intended state:** Production-ready packages that can be seamlessly published to PyPI and npm with correct dependencies, exports, and documentation.
**Why it matters:** Incomplete packaging hinders adoption and makes it difficult for other projects to cleanly depend on the library.
**Recommended next action:** Refine `setup.py`, `package.json`, and related metadata to align with standard publishing best practices for each ecosystem.


## Resolved Gaps

### Browser/sql.js malformed provider_config_json corruption test exception

**Status:** Documented Exception (Resolved)
**Area:** Testing
**Current state:** Python and Node.js file-backed SQLite implementations use `PRAGMA ignore_check_constraints = ON` to verify that the public API handles malformed JSON in `provider_config_json` (corruption on disk) gracefully by raising `InvalidStorageFormat`. `browser-test` skips this direct corruption test because `sql.js` schema constraints strictly block malformed JSON via `CHECK(json_valid(...))` and bypassing it via PRAGMA is not a required conformance path for the browser implementation.
**Expected or intended state:** The browser-test exception is fully documented. Semantic invalid JSON cases (which bypass the schema constraint) are universally tested across all environments.
**Why it matters:** Clearly defines that this is a test-scope exception rather than a missing compatibility guarantee.
**Recommended next action:** None.


### Storage-format-v1 validation policy parity

**Status:** Resolved
**Area:** Storage Format
**Current state:** Python, Node.js, and browser-test implementations have unified validation policies for Storage Format V1. All strictly validate `storage_metadata_tbl` exactness, `database_uuid` canonical form, and `provider_config_json` JCS exactness and explicit parameters. Direct SQL `CHECK` constraint tests are primary coverage in Python / Node.js. Browser-test may have representative sql.js constraint tests, but it does not need to be described as full file-backed parity.
**Expected or intended state:** Strict structural parity ensures cross-language implementation correctness. `created_by_library` and `created_by_version` are validated as diagnostic provenance metadata strings (not compatibility gates) to preserve interoperability.
**Why it matters:** Parity ensures consistent data safety guarantees and bug-free interoperability.
**Recommended next action:** None.

### Browser/sql.js PRAGMA validation exception

**Status:** Documented Exception (Resolved)
**Area:** Storage Format
**Current state:** `browser-test` bypasses `PRAGMA application_id` and `PRAGMA user_version` validations due to `sql.js` in-memory behavior, instead relying entirely on `storage_metadata_tbl` as the authoritative source. This is explicitly documented in the SQLite Profile specification.
**Expected or intended state:** The exception is documented and covered by specific tests.
**Why it matters:** Prevents browser export/import flows from incorrectly triggering format validation failures.
**Recommended next action:** None.

### Storage format v1 identity and metadata handling

**Status:** Resolved
**Area:** Storage Format
**Current state:** Python, Node.js, and browser-test implementations fully support parsing, validating, and writing Storage Format V1 metadata. This includes `storage_metadata_tbl`, `PRAGMA application_id`, JCS canonical exactness checking for features, and pre-V1 database explicit rejection.
**Expected or intended state:** Application code initializes V1 databases with proper metadata and respects/enforces the format identity and strict feature rejection policies. Pre-V1 databases are explicitly rejected.
**Why it matters:** Without these metadata handling mechanisms, forward/backward compatibility and feature flag protections cannot be guaranteed.
**Recommended next action:** None.

### SQLite storage profile v1 metadata implementation

**Status:** Resolved
**Area:** Storage Format
**Current state:** Python, Node.js, and browser-test implementations strictly validate `PRAGMA application_id` and `PRAGMA user_version` (with an explicit, documented exception for the browser-test sql.js in-memory database). The SQLite schema fully matches the v1 profile.
**Expected or intended state:** The SQLite schema fully matches the v1 profile.
**Why it matters:** The physical database layout must support format versioning.
**Recommended next action:** None.

### Metadata/versioning table

**Status:** Resolved
**Area:** Storage Format
**Current state:** The `schema.sql` includes the `storage_metadata_tbl`. Implementations properly initialize it with JCS canonical JSON feature flags and required version strings.
**Expected or intended state:** A dedicated `storage_metadata_tbl` exists and is populated during database initialization.
**Why it matters:** Essential for the Versioning and Compatibility Policy.
**Recommended next action:** None.

### Schema constraints for v1 invariants

**Status:** Resolved
**Area:** Storage Format
**Current state:** `CHECK` constraints for 12-byte nonces, wrapped key minimum lengths, ciphertext minimum lengths, and non-empty content types have been added to `schema.sql`. Direct SQL `CHECK` constraint tests are primary coverage in Python / Node.js. Browser-test has representative sql.js constraint tests, but intentionally skips full file-backed parity (e.g. malformed-on-disk corruption via `ignore_check_constraints` is a documented test-scope exception).
**Expected or intended state:** The schema uses implemented SQLite `CHECK` constraints to provide defense-in-depth for V1 invariants.
**Why it matters:** DBMS-level enforcement prevents corruption from external tools or bugs in the application layer.
**Recommended next action:** None.

### Provider Config Explicitness

**Status:** Resolved
**Area:** Storage Format
**Current state:** `provider_config_json` explicitly stores `kdf`, `profile`, `output_bytes`, `memory_kib`, `iterations`, `parallelism`, and `salt`. Validations require strict JCS canonical exactness, exact profile matching, and exact parameter matching for Argon2id Profile V1.
**Expected or intended state:** The initialization logic writes a fully explicit `provider_config_json` block for the `passphrase_argon2id` provider.
**Why it matters:** Implicit parameters risk long-term compatibility issues.
**Recommended next action:** None.


### Cross-language cryptographic test vectors are not materially implemented

**Status:** Resolved
**Area:** Cryptography / Interoperability
**Current state:** Comprehensive suites of cross-language test vectors have been implemented across Python, Node.js, and browser-test environments. This includes JCS canonicalization (`test-vectors/jcs`), AAD policies (`test-vectors/aad`), Argon2id KDF (`test-vectors/kdf`), AES-256-GCM primitives (`test-vectors/aead`), key-wrapping (`test-vectors/key-wrap`), and payload encryption (`test-vectors/payload`). Byte-for-byte equivalence is validated by automated test suites. Browser-test Jest environments validate the same shared vectors. AEAD primitive checks currently use Node.js crypto in the Jest environment and do not fully verify a real browser WebCrypto runtime path.
**Expected or intended state:** A comprehensive suite of cross-language test vectors ensuring byte-for-byte equivalence for all cryptographic and key-derivation operations.
**Why it matters:** Without shared test vectors, implementations might subtly diverge in cryptographic implementations, resulting in data that cannot be decrypted across platforms.
**Recommended next action:** None. Resolved via addition of machine-readable JSON test vectors and corresponding language test suites.

### Platform-specific Argon2id Parameters

**Status:** Resolved
**Area:** Cryptography / Security
**Current state:** Python, Node.js, and browser environments now universally use the platform-independent `ARGON2ID_PROFILE_V1` parameters (65536 KiB memory, 3 iterations, 1 parallelism, 16 salt bytes, 32 output bytes) when initializing a new database.
**Expected or intended state:** All platforms use the identical profile, relying on provider configuration records for compatibility, without resorting to platform-specific parameter branching.
**Why it matters:** Inconsistent parameters across platforms create branching logic and test divergence, breaking unified security expectations.
**Recommended next action:** None. Resolved via unification.

### SQLite roundtrip interoperability coverage

**Status:** Partially Resolved
**Area:** Cryptography / Interoperability
**Current state:** Fully automated Python ↔ Node.js roundtrip integration tests exist in `integration-tests/roundtrip` and are executed by the GitHub Actions integration workflow. Browser DB export/import interoperability and Go/Rust roundtrip coverage remain future work.
**Expected or intended state:** Automated tests ensuring DB files created in one platform can be successfully read and decrypted in another.
**Why it matters:** Interoperability is the core value proposition of the library.
**Recommended next action:** Expand to include browser interoperability tests.

### Coverage badge publication

**Status:** Resolved
**Area:** Testing / CI
**Current state:** Codecov upload steps are configured in Python / Node.js / browser-test workflows. Upload uses OIDC via `use_oidc: true` and `id-token: write`. Coverage is segmented by Codecov flags (`python`, `nodejs`, `browser-test`). GitHub Actions coverage artifacts are still preserved. The top-level README now includes an overall Codecov coverage badge.
**Expected or intended state:** Coverage badges correctly display on the `README.md` using the verified Codecov badge URL.
**Why it matters:** Good visibility into CI test coverage encourages maintainability and testing standards.
**Recommended next action:** None. Future hardening may include per-flag badges, coverage thresholds, or Codecov status checks.

### Browser real-runtime coverage not implemented

**Status:** Active
**Area:** Testing
**Current state:** The browser-test harness achieves high logical coverage, but because it relies on `jest-environment-jsdom` and Node's simulated `crypto`, it does not currently measure true browser real-runtime execution paths (like WebCrypto inside an actual headless browser).
**Expected or intended state:** Coverage metrics that accurately reflect real browser environments (e.g. via Playwright or Puppeteer).
**Why it matters:** Logical coverage in Node.js does not guarantee compatibility or execution safety inside a restricted Web Worker or browser environment.
**Recommended next action:** Expand `browser-test` tooling to incorporate headless browser tests for coverage metrics.


### Go and Rust portability implementation gaps

**Status:** Active
**Area:** Cryptography / Interoperability
**Current state:** Go and Rust implementations now include cryptographic conformance validation against shared vectors, and a SQLite V1 read-only metadata validator. However, they are still portability validation scaffolds and lack full storage library implementation, database unlock/decrypt readers, writers, and cross-language roundtrip integration.
**Expected or intended state:** Go and Rust implementations are complete, production-ready storage libraries integrated into the cross-language roundtrip matrix.
**Why it matters:** Required to establish true portability and multi-language support.
**Recommended next action:** Implement database unlock and decrypt reader for Go and Rust.
