# Implementation Gaps

This document tracks known discrepancies and gaps between the current specifications/decisions and the existing codebase.

## Active Gaps



### 1. JWE/JOSE compatibility is not implemented

**Status:** Active
**Area:** Standards Compatibility
**Current state:** The envelope format defined in `docs/spec/envelope-format.md` is custom and AEAD-oriented. It resembles JOSE/JWE concepts but is not a valid JWE serialization.
**Expected or intended state:** Documented clarity that JWE compatibility is not natively supported, but potentially provided via an export/adapter pattern.
**Why it matters:** Developers might incorrectly assume the library produces standard JWE tokens, leading to integration issues with external systems.
**Recommended next action:** Update documentation to clarify the non-JWE nature of the envelopes, and treat standard JWE export as a future enhancement rather than a current feature.

### 2. Key rotation and lifecycle operations are not implemented

**Status:** Active
**Area:** Key Management
**Current state:** The schema supports `status`, activation/deactivation timestamps, and key classes, but public operations for key rotation, decrypt-only migration, destruction semantics, and rewrapping are not implemented.
**Expected or intended state:** Public APIs allowing consumers to securely rotate keys, rewrap data, and manage key lifecycles according to the schema capabilities.
**Why it matters:** Lack of key rotation makes the library unsuitable for long-term production use where cryptographic hygiene and rotation are mandated.
**Recommended next action:** Specify and implement key rotation, migration, and key destruction procedures.

### 3. Additional unlock providers are schema/planned only

**Status:** Active
**Area:** Features
**Current state:** The schema lists multiple unlock methods and provider concepts, but only the passphrase (Argon2id) provider is currently implemented.
**Expected or intended state:** Implementation of, or clear documentation that other providers (OS secret store, hardware token, remote KMS, Shamir/threshold recovery) are strictly planned future features.
**Why it matters:** Users may be confused by schema references to features that are entirely non-functional in the library.
**Recommended next action:** Clearly document these as planned features or stub them out in the API contract.

### 4. Blind index implementation is not complete

**Status:** Active
**Area:** Features
**Current state:** `docs/spec/blind-index.md` outlines HMAC-based blind indexes, but no corresponding API, tables, or tests exist in the current implementations.
**Expected or intended state:** A functional blind index API allowing searchable encrypted data.
**Why it matters:** Without blind indexes, the database cannot easily be queried based on payload contents, severely limiting its utility as a database.
**Recommended next action:** Implement the schema tables and API methods for blind indexes according to the specification.

### 5. Input validation and canonicalization boundaries need hardening

**Status:** Partially Resolved
**Area:** Security / Input Validation
**Current state:** UUID formats and content types are now validated at the public API boundary in Python, Node.js, and browser-test environments before reaching SQLite constraints. Payload validation has improved, but strict plain-JSON-object enforcement across all implementations is still incomplete. Stricter MIME type parsing and full JSON Schema semantic validations remain future work.
**Expected or intended state:** Strict input validation and normalization at the public API boundary before interacting with the database.
**Why it matters:** Relying solely on database constraints can lead to unhandled database errors bubbling up instead of providing clear, early validation errors to the caller.
**Recommended next action:** Complete strict payload validation hardening across implementations, implement stricter MIME type parsing, and evaluate whether JSON Schema validation is within scope or out of scope.

### 6. Packaging and distribution maturity is incomplete

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
**Current state:** Comprehensive suites of cross-language test vectors have been implemented across Python, Node.js, and browser-test environments. This includes JCS canonicalization (`test-vectors/jcs`), AAD policies (`test-vectors/aad`), Argon2id KDF (`test-vectors/kdf`), AES-256-GCM primitives (`test-vectors/aead`), key-wrapping (`test-vectors/key-wrap`), and payload encryption (`test-vectors/payload`). Byte-for-byte equivalence is validated by automated test suites. Browser-test environments utilize Jest tests using the same shared vectors, testing the browser bundle crypto path logic, rather than fully verifying a real browser WebCrypto runtime path.
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
