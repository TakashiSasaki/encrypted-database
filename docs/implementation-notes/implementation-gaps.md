# Implementation Gaps

This document tracks known discrepancies and gaps between the current specifications/decisions and the existing codebase.

## Active Gaps

### 1. Storage format v1 draft is not fully implemented

**Status:** Draft / Active
**Area:** Storage Format
**Current state:** `docs/spec/storage-format.md` outlines a draft for the v1 storage format core, including identity, versioning policies, and feature flags. However, the application code does not yet implement the reading, writing, or handling of these new v1 metadata constructs.
**Expected or intended state:** Application code respects and enforces the format identity, required/optional features, and compatibility policies defined in the v1 draft.
**Why it matters:** Without these metadata handling mechanisms, forward/backward compatibility and feature flag protections cannot be guaranteed.
**Recommended next action:** Implement the format identity parsing and rejection logic according to the draft specification.

### 2. SQLite storage profile v1 is not fully implemented

**Status:** Draft / Active
**Area:** Storage Format
**Current state:** `docs/spec/storage-format-sqlite.md` outlines the physical SQLite profile for the v1 draft. The current database schema lacks the necessary structures to support the full v1 profile requirements.
**Expected or intended state:** The SQLite schema fully matches the finalized v1 profile.
**Why it matters:** The physical database layout is currently missing critical components required for format versioning.
**Recommended next action:** Update the schema and application queries to conform to the completed v1 SQLite profile.

### 3. Metadata/versioning table is not implemented

**Status:** Draft / Active
**Area:** Storage Format
**Current state:** The current `schema.sql` lacks a table (e.g., `metadata_tbl`) to store format version numbers, required features, optional features, and the database UUID.
**Expected or intended state:** A dedicated metadata table exists and is populated during database initialization.
**Why it matters:** Essential for the Versioning and Compatibility Policy.
**Recommended next action:** Design and add a `metadata_tbl` to the schema.

### 4. Schema constraints for v1 invariants are not finalized

**Status:** Draft / Active
**Area:** Storage Format
**Current state:** While the abstract storage format specifies invariants like 12-byte nonces and non-empty content types, the current SQLite schema does not use available `CHECK` constraints (e.g., `length(nonce) = 12`) to enforce them at the DBMS level, relying purely on application logic.
**Expected or intended state:** The schema utilizes appropriate SQLite `CHECK` constraints to provide defense-in-depth for V1 invariants.
**Why it matters:** DBMS-level enforcement prevents corruption from external tools or bugs in the application layer.
**Recommended next action:** Finalize and add the missing `CHECK` constraints to `schema.sql`.

### 5. Go and Rust implementations are planned but not implemented

**Status:** Active
**Area:** Implementation
**Current state:** Python, Node.js, and browser-test implementations exist. Go and Rust implementations are planned to prove the portability of the storage format but do not yet exist.
**Expected or intended state:** Native Go and Rust packages exist and pass all cross-language test vectors.
**Why it matters:** The storage format core is designed for multi-language support. Proving it in strictly-typed, compiled languages (Go/Rust) is crucial for V1 stabilization.
**Recommended next action:** Create initial scaffolding for the Go module and Rust crate.

### 6. Roundtrip matrix does not yet include Go/Rust

**Status:** Active
**Area:** Interoperability
**Current state:** Semantic SQLite roundtrip tests exist between Python and Node.js.
**Expected or intended state:** The roundtrip test matrix tests database creation, unlocking, reading, and writing across all supported languages (Python, Node.js, Go, Rust) and browser exports.
**Why it matters:** To guarantee true V1 interoperability.
**Recommended next action:** Expand the `test_roundtrip.sh` harness once Go/Rust implementations are viable.

### 7. JWE/JOSE compatibility is not implemented

**Status:** Active
**Area:** Standards Compatibility
**Current state:** The envelope format defined in `docs/spec/envelope-format.md` is custom and AEAD-oriented. It resembles JOSE/JWE concepts but is not a valid JWE serialization.
**Expected or intended state:** Documented clarity that JWE compatibility is not natively supported, but potentially provided via an export/adapter pattern.
**Why it matters:** Developers might incorrectly assume the library produces standard JWE tokens, leading to integration issues with external systems.
**Recommended next action:** Update documentation to clarify the non-JWE nature of the envelopes, and treat standard JWE export as a future enhancement rather than a current feature.

### 8. Key rotation and lifecycle operations are not implemented

**Status:** Active
**Area:** Key Management
**Current state:** The schema supports `status`, activation/deactivation timestamps, and key classes, but public operations for key rotation, decrypt-only migration, destruction semantics, and rewrapping are not implemented.
**Expected or intended state:** Public APIs allowing consumers to securely rotate keys, rewrap data, and manage key lifecycles according to the schema capabilities.
**Why it matters:** Lack of key rotation makes the library unsuitable for long-term production use where cryptographic hygiene and rotation are mandated.
**Recommended next action:** Specify and implement key rotation, migration, and key destruction procedures.

### 9. Additional unlock providers are schema/planned only

**Status:** Active
**Area:** Features
**Current state:** The schema lists multiple unlock methods and provider concepts, but only the passphrase (Argon2id) provider is currently implemented.
**Expected or intended state:** Implementation of, or clear documentation that other providers (OS secret store, hardware token, remote KMS, Shamir/threshold recovery) are strictly planned future features.
**Why it matters:** Users may be confused by schema references to features that are entirely non-functional in the library.
**Recommended next action:** Clearly document these as planned features or stub them out in the API contract.

### 10. Blind index implementation is not complete

**Status:** Active
**Area:** Features
**Current state:** `docs/spec/blind-index.md` outlines HMAC-based blind indexes, but no corresponding API, tables, or tests exist in the current implementations.
**Expected or intended state:** A functional blind index API allowing searchable encrypted data.
**Why it matters:** Without blind indexes, the database cannot easily be queried based on payload contents, severely limiting its utility as a database.
**Recommended next action:** Implement the schema tables and API methods for blind indexes according to the specification.

### 11. Input validation and canonicalization boundaries need hardening

**Status:** Partially Resolved
**Area:** Security / Input Validation
**Current state:** UUID formats, content types, and payloads are strictly validated at the public API boundary. Deep payload type checking is fully implemented, recursively rejecting raw buffers, typed arrays, and non-JSON values prior to canonicalization across Python, Node.js, and browser environments. Passphrase type invalidity is uniformly validated with a dedicated `InvalidPassphrase` error across all environments. The `StorageClosed` error correctly takes precedence over input validation errors on closed resources. Stricter MIME type parsing, full JSON Schema semantic validation, UUID registry semantic validation, and UI-level feedback in the browser demo remain future work.
**Expected or intended state:** Strict input validation and normalization at the public API boundary before interacting with the database.
**Why it matters:** Relying solely on database constraints can lead to unhandled database errors bubbling up instead of providing clear, early validation errors to the caller.
**Recommended next action:** Implement stricter MIME type parsing, and evaluate whether JSON Schema and UUID registry validations are within scope or out of scope.

### 12. Packaging and distribution maturity is incomplete

**Status:** Active
**Area:** Deployment
**Current state:** Python and Node.js packaging metadata, exports, versioning, and setup scripts are present but lack the polish required for production publishing (e.g., missing comprehensive exports, mismatched versions, and incomplete README examples).
**Expected or intended state:** Production-ready packages that can be seamlessly published to PyPI and npm with correct dependencies, exports, and documentation.
**Why it matters:** Incomplete packaging hinders adoption and makes it difficult for other projects to cleanly depend on the library.
**Recommended next action:** Refine `setup.py`, `package.json`, and related metadata to align with standard publishing best practices for each ecosystem.


## Resolved Gaps

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
**Current state:** Fully automated Python ↔ Node.js roundtrip integration tests exist in `integration-tests/roundtrip` and ensure cross-platform database semantic equivalence. Note that these tests are not yet fully integrated into the standard CI workflows. Browser DB export/import interoperability remains future work.
**Expected or intended state:** Automated tests ensuring DB files created in one platform can be successfully read and decrypted in another.
**Why it matters:** Interoperability is the core value proposition of the library.
**Recommended next action:** Expand to include browser interoperability tests.
