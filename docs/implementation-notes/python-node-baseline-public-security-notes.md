# Python/Node.js Baseline-Public Candidate Security Notes

## Purpose
This document provides the security and readiness notes for the Python and Node.js baseline-public candidates. It highlights assumptions, limitations, and boundaries. It is **not** a completed security audit.

## Cryptography and Key Management
- **Passphrase Handling & Argon2id Profile:** The libraries derive the Key Encryption Key (KEK) using Argon2id with strict parameters (Time Cost 3, Memory Cost 64 MiB, Parallelism 1, Salt Length 16 bytes).
- **No Passphrase Logging:** Passphrases are never logged. The internal states strictly zeroize or discard references as early as possible within the limits of the runtime garbage collectors.
- **KEK Lifecycle:** The KEK resides in memory while unlocked. It relies on the environment's memory protection.
- **Lock/Close Semantics:** `lock()` removes the KEK from active memory logic, rendering the storage inert. `close()` shuts down the underlying database connection.
- **AES-256-GCM Envelope:** Payload encryption strictly uses AES-256-GCM. The envelope layout, IVs, and MACs are stable.
- **AAD Policy Dependency:** Authenticated Additional Data (AAD) is strictly tied to the object metadata. Any mismatch during retrieval throws an `AadPolicyError` or `IntegrityCheckFailed`.

## Payloads and Content Types
- **Payload Boundaries:** The library enforces JSON Canonicalization Scheme (JCS) semantics on object serialization. The caller is responsible for providing valid UTF-8 strings or structural payload data.
- **Safe Integer / JSON Number Caveat:** Float values and unsafe large integers are inherently problematic across platforms. The libraries enforce strict boundaries rejecting out-of-bounds numbers and floating-point ambiguity where identifiable.

## Storage Backend
- **SQLite Profile Expectations:** The schema heavily relies on foreign keys (`PRAGMA foreign_keys = ON`), strict typing, and specific table layouts. Modifying the generated tables outside the library is unsupported and may trigger integrity failures.
- **Diagnostic Provenance:** `created_by_version` metadata is diagnostic only; it does not serve as a cryptographic or compatibility gate.

## Unsupported Features
The following capabilities are explicitly unsupported in this implementation phase:
- Key rotation
- Database rewrap
- Database destroy capabilities
- Additional unlock providers
- Blind indexes
- Browser real-runtime coverage
- C/C++ storage APIs

## Current Evidence vs. Remaining Release Blockers
The Python and Node.js libraries currently satisfy cross-language testing requirements via public-entrypoint test-wrappers and shared vector tests. However, formal security sign-off, API freeze confirmation, and removal of test-wrapper specific compatibility gates remain as blockers prior to full baseline-public certification.
