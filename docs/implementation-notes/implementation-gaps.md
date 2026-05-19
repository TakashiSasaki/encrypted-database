# Implementation Gaps

This document tracks known discrepancies and gaps between the current specifications/decisions and the existing codebase.

## Active Gaps

### 1. Public API contract is not yet specified

**Status:** Partially Resolved
**Area:** API / cross-language compatibility
**Current state:** A canonical `docs/spec/api-contract.md` exists, detailing lifecycle states, lock/close behavior, status queries, and error categories. Sync/async semantics and provider behaviors might still need further elaboration in the spec.
**Expected or intended state:** A formal specification defining the exact inputs, outputs, and side effects of each public method to ensure parity across all language implementations.
**Why it matters:** Without a canonical API contract, language implementations may diverge, leading to an inconsistent and unpredictable developer experience.
**Recommended next action:** Expand the API contract to document provider behavior, sync/async nuances across environments, and UUID normalization rules.

### 2. Error taxonomy is not implemented

**Status:** Active
**Area:** Error Handling
**Current state:** Python currently raises generic exceptions (`ValueError`), and Node.js throws generic `Error` objects for public failures. Tests rely on error message string matching.
**Expected or intended state:** A library-quality API defining stable typed errors or error codes (e.g., `StorageLocked`, `UnlockFailed`, `ObjectNotFound`, `UnsupportedPlatform`).
**Why it matters:** Consumers of the library cannot easily handle programmatic failures or distinguish between different error conditions without brittle string matching.
**Recommended next action:** Define a standardized list of error codes in the API contract and implement corresponding custom error classes across Python and Node.js.

### 3. Lock/close lifecycle is incomplete

**Status:** Resolved
**Area:** Lifecycle Management
**Current state:** A clear lifecycle has been implemented across Python, Node.js, and Browser implementations. The API correctly transitions between `uninitialized`, `open_locked`, `open_unlocked`, and `closed`. `lock()`, `close()`, `is_unlocked()`, `is_closed()`, and `get_status()` operations exist and behave identically.
**Expected or intended state:** A robust lifecycle management API with clear transitions between locked and unlocked states, along with public status check methods.
**Why it matters:** Callers cannot easily query the current state of the database, making it difficult to build resilient applications on top of the library.
**Recommended next action:** Keep monitoring browser-specific backend initialization lifecycle edges if browser adapter support evolves.

### 4. Cross-language cryptographic test vectors are not materially implemented

**Status:** Partially Resolved
**Area:** Cryptography / Interoperability
**Current state:** JCS canonicalization and AAD vectors are fully implemented and verified via shared cross-language test suites in `test-vectors/jcs` and `test-vectors/aad`. However, there are no machine-readable test vectors for Argon2id, AES-GCM, fixed nonce, and fixed salt operations.
**Expected or intended state:** A comprehensive suite of cross-language test vectors ensuring byte-for-byte equivalence for all cryptographic and key-derivation operations.
**Why it matters:** Without shared test vectors, implementations might subtly diverge in cryptographic implementations, resulting in data that cannot be decrypted across platforms.
**Recommended next action:** Generate and commit additional JSON datasets for KDF, AEAD, key-wrap, and payload encryption operations.

### 5. SQLite roundtrip interoperability is not yet demonstrated

**Status:** Active
**Area:** Cross-language portability
**Current state:** Python and Node.js can each store and retrieve payloads independently, but there are no tests demonstrating that a database created in Python can be successfully read by Node.js, and vice versa.
**Expected or intended state:** Automated tests validating cross-language compatibility of the resulting SQLite database files.
**Why it matters:** The primary goal of a shared SQLite backend is portability. Without roundtrip tests, subtle differences in how platforms interact with SQLite may cause data corruption or read failures.
**Recommended next action:** Implement cross-language end-to-end tests that generate a database in one language and verify it in the others.

### 6. JWE/JOSE compatibility is not implemented

**Status:** Active
**Area:** Standards Compatibility
**Current state:** The envelope format defined in `docs/spec/envelope-format.md` is custom and AEAD-oriented. It resembles JOSE/JWE concepts but is not a valid JWE serialization.
**Expected or intended state:** Documented clarity that JWE compatibility is not natively supported, but potentially provided via an export/adapter pattern.
**Why it matters:** Developers might incorrectly assume the library produces standard JWE tokens, leading to integration issues with external systems.
**Recommended next action:** Update documentation to clarify the non-JWE nature of the envelopes, and treat standard JWE export as a future enhancement rather than a current feature.

### 7. Key rotation and lifecycle operations are not implemented

**Status:** Active
**Area:** Key Management
**Current state:** The schema supports `status`, activation/deactivation timestamps, and key classes, but public operations for key rotation, decrypt-only migration, destruction semantics, and rewrapping are not implemented.
**Expected or intended state:** Public APIs allowing consumers to securely rotate keys, rewrap data, and manage key lifecycles according to the schema capabilities.
**Why it matters:** Lack of key rotation makes the library unsuitable for long-term production use where cryptographic hygiene and rotation are mandated.
**Recommended next action:** Specify and implement key rotation, migration, and key destruction procedures.

### 8. Additional unlock providers are schema/planned only

**Status:** Active
**Area:** Features
**Current state:** The schema lists multiple unlock methods and provider concepts, but only the passphrase (Argon2id) provider is currently implemented.
**Expected or intended state:** Implementation of, or clear documentation that other providers (OS secret store, hardware token, remote KMS, Shamir/threshold recovery) are strictly planned future features.
**Why it matters:** Users may be confused by schema references to features that are entirely non-functional in the library.
**Recommended next action:** Clearly document these as planned features or stub them out in the API contract.

### 9. Blind index implementation is not complete

**Status:** Active
**Area:** Features
**Current state:** `docs/spec/blind-index.md` outlines HMAC-based blind indexes, but no corresponding API, tables, or tests exist in the current implementations.
**Expected or intended state:** A functional blind index API allowing searchable encrypted data.
**Why it matters:** Without blind indexes, the database cannot easily be queried based on payload contents, severely limiting its utility as a database.
**Recommended next action:** Implement the schema tables and API methods for blind indexes according to the specification.

### 10. Input validation and canonicalization boundaries need hardening

**Status:** Active
**Area:** Security / Input Validation
**Current state:** UUID formats are enforced via SQLite `CHECK` constraints, but public APIs do not consistently normalize or reject invalid UUIDs before database operations. `content_type` validation is minimal.
**Expected or intended state:** Strict input validation and normalization at the public API boundary before interacting with the database.
**Why it matters:** Relying solely on database constraints can lead to unhandled database errors bubbling up instead of providing clear, early validation errors to the caller.
**Recommended next action:** Add rigorous input validation and normalization steps to all public API endpoints.

### 11. Packaging and distribution maturity is incomplete

**Status:** Active
**Area:** Deployment
**Current state:** Python and Node.js packaging metadata, exports, versioning, and setup scripts are present but lack the polish required for production publishing (e.g., missing comprehensive exports, mismatched versions, and incomplete README examples).
**Expected or intended state:** Production-ready packages that can be seamlessly published to PyPI and npm with correct dependencies, exports, and documentation.
**Why it matters:** Incomplete packaging hinders adoption and makes it difficult for other projects to cleanly depend on the library.
**Recommended next action:** Refine `setup.py`, `package.json`, and related metadata to align with standard publishing best practices for each ecosystem.
