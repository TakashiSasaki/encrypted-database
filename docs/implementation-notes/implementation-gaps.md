# Implementation Gaps

This document tracks known discrepancies and gaps between the current specifications/decisions and the existing codebase.

## Active Gaps

### 1. Cross-language cryptographic test vectors are not materially implemented

**Status:** Resolved
**Area:** Cryptography / Interoperability
**Current state:** A comprehensive suite of machine-readable cross-language test vectors ensuring byte-for-byte equivalence for all cryptographic and key-derivation operations is fully implemented. Vectors for Argon2id KDF, AES-GCM, key-wrap, payload encryption, JCS canonicalization, and AAD contexts are verified symmetrically across Python, Node.js, and browser-test implementations via shared JSON datasets in `test-vectors/`.
**Expected or intended state:** A comprehensive suite of cross-language test vectors ensuring byte-for-byte equivalence for all cryptographic and key-derivation operations.
**Why it matters:** Without shared test vectors, implementations might subtly diverge in cryptographic implementations, resulting in data that cannot be decrypted across platforms.
**Recommended next action:** N/A

### 2. JWE/JOSE compatibility is not implemented

**Status:** Active
**Area:** Standards Compatibility
**Current state:** The envelope format defined in `docs/spec/envelope-format.md` is custom and AEAD-oriented. It resembles JOSE/JWE concepts but is not a valid JWE serialization.
**Expected or intended state:** Documented clarity that JWE compatibility is not natively supported, but potentially provided via an export/adapter pattern.
**Why it matters:** Developers might incorrectly assume the library produces standard JWE tokens, leading to integration issues with external systems.
**Recommended next action:** Update documentation to clarify the non-JWE nature of the envelopes, and treat standard JWE export as a future enhancement rather than a current feature.

### 3. Key rotation and lifecycle operations are not implemented

**Status:** Active
**Area:** Key Management
**Current state:** The schema supports `status`, activation/deactivation timestamps, and key classes, but public operations for key rotation, decrypt-only migration, destruction semantics, and rewrapping are not implemented.
**Expected or intended state:** Public APIs allowing consumers to securely rotate keys, rewrap data, and manage key lifecycles according to the schema capabilities.
**Why it matters:** Lack of key rotation makes the library unsuitable for long-term production use where cryptographic hygiene and rotation are mandated.
**Recommended next action:** Specify and implement key rotation, migration, and key destruction procedures.

### 4. Additional unlock providers are schema/planned only

**Status:** Active
**Area:** Features
**Current state:** The schema lists multiple unlock methods and provider concepts, but only the passphrase (Argon2id) provider is currently implemented.
**Expected or intended state:** Implementation of, or clear documentation that other providers (OS secret store, hardware token, remote KMS, Shamir/threshold recovery) are strictly planned future features.
**Why it matters:** Users may be confused by schema references to features that are entirely non-functional in the library.
**Recommended next action:** Clearly document these as planned features or stub them out in the API contract.

### 5. Blind index implementation is not complete

**Status:** Active
**Area:** Features
**Current state:** `docs/spec/blind-index.md` outlines HMAC-based blind indexes, but no corresponding API, tables, or tests exist in the current implementations.
**Expected or intended state:** A functional blind index API allowing searchable encrypted data.
**Why it matters:** Without blind indexes, the database cannot easily be queried based on payload contents, severely limiting its utility as a database.
**Recommended next action:** Implement the schema tables and API methods for blind indexes according to the specification.

### 6. Input validation and canonicalization boundaries need hardening

**Status:** Active
**Area:** Security / Input Validation
**Current state:** UUID formats are enforced via SQLite `CHECK` constraints, but public APIs do not consistently normalize or reject invalid UUIDs before database operations. `content_type` validation is minimal.
**Expected or intended state:** Strict input validation and normalization at the public API boundary before interacting with the database.
**Why it matters:** Relying solely on database constraints can lead to unhandled database errors bubbling up instead of providing clear, early validation errors to the caller.
**Recommended next action:** Add rigorous input validation and normalization steps to all public API endpoints.

### 7. Packaging and distribution maturity is incomplete

**Status:** Active
**Area:** Deployment
**Current state:** Python and Node.js packaging metadata, exports, versioning, and setup scripts are present but lack the polish required for production publishing (e.g., missing comprehensive exports, mismatched versions, and incomplete README examples).
**Expected or intended state:** Production-ready packages that can be seamlessly published to PyPI and npm with correct dependencies, exports, and documentation.
**Why it matters:** Incomplete packaging hinders adoption and makes it difficult for other projects to cleanly depend on the library.
**Recommended next action:** Refine `setup.py`, `package.json`, and related metadata to align with standard publishing best practices for each ecosystem.


## Resolved Gaps

### SQLite roundtrip interoperability coverage

**Status:** Resolved
**Area:** Cryptography / Interoperability
**Current state:** Fully automated Python ↔ Node.js roundtrip integration tests exist in `integration-tests/roundtrip` and ensure cross-platform database semantic equivalence. Browser DB export/import interoperability remains future work.
**Expected or intended state:** Automated tests ensuring DB files created in one platform can be successfully read and decrypted in another.
**Why it matters:** Interoperability is the core value proposition of the library.
**Recommended next action:** Expand to include browser interoperability tests.
