# Python and Node.js Baseline-Public API and Error Semantics Audit

## Purpose
This document provides a side-by-side audit of the Python and Node.js public-facing storage APIs and their error semantics. It evaluates the parity status that was required before the implementations were promoted to `baseline-public`.

## API Parity Status

Parity status is classified using the following vocabulary:
- `aligned`: Behavior and signature are semantically identical or map cleanly across language idioms.
- `minor-naming-difference`: Small naming differences (e.g., snake_case vs camelCase) that are accepted language conventions.
- `semantics-unclear`: The expected behavior is not strictly defined or diverges in subtle ways.
- `missing-test-coverage`: The API exists but lacks explicit tests verifying cross-language parity.
- `implementation-gap`: One language implements the API or behavior, but the other does not.
- `needs-decision`: Requires a design decision before locking the public API.
- `out-of-scope`: Not applicable or not planned for the baseline-public milestone.

### Core Lifecycle API

| API/Behavior | Python | Node.js | Parity Status | Notes |
|---|---|---|---|---|
| Instantiation | `EncryptedStorage(db_path)` | `new EncryptedStorage(db_path)` | aligned | Synchronous instantiation. |
| Database Initialization | `initialize_database(passphrase, platform)` | `initializeDatabase(passphrase, platform)` | aligned | Synchronous in Python, async in Node.js due to Argon2. |
| Database Unlock | `unlock_database(passphrase)` | `unlockDatabase(passphrase)` | aligned | Synchronous in Python, async in Node.js due to Argon2. |
| Payload Storage | `store_payload(schema_uuid, content_type, payload)` | `storePayload(schemaUuid, contentType, payload)` | aligned | Both return the new `object_uuid`. |
| Payload Retrieval | `retrieve_payload(object_uuid)` | `retrievePayload(objectUuid)` | aligned | |
| Payload Update | `update_payload(object_uuid, schema_uuid, content_type, payload)` | `updatePayload(objectUuid, schemaUuid, contentType, payload)` | aligned | |
| Payload Deletion | `delete_payload(object_uuid)` | `deletePayload(objectUuid)` | aligned | |
| Database Status | `get_status()` | `getStatus()` | aligned | Returns `"closed"`, `"open_unlocked"`, `"uninitialized"`, or `"open_locked"`. |
| Database Lock | `lock()` | `lock()` | aligned | Forgets the active KEK. |
| Database Close | `close()` | `close()` | aligned | |
| Check if closed | `is_closed()` | `isClosed()` | aligned | |
| Check if unlocked | `is_unlocked()` | `isUnlocked()` | aligned | |

### Parameters & Types

| Parameter / Concept | Python | Node.js | Parity Status | Notes |
|---|---|---|---|---|
| Passphrase handling | `str` | `string` | aligned | Enforces string type. |
| Schema UUID handling | `str` | `string` | aligned | Validated as canonical lowercase hyphenated UUID. |
| Object UUID handling | `str` | `string` | aligned | Validated as canonical lowercase hyphenated UUID. |
| Content type handling | `str` | `string` | aligned | Validated for non-empty, contains `/`, no control chars. |
| Payload type | `dict` (JSON-serializable) | `object` (JSON-serializable) | aligned | Both enforce JCS normalization and reject functions/cycles. |
| Platform argument | `str` (e.g., "linux") | `string` | aligned | Rejects `"cross_platform"` and unknown platforms. |

## Error Semantics Audit

Python uses exception classes in `encrypted_storage.errors`. Node.js uses matching exception classes in `errors.js`.

| Error Case | Python Exception | Node.js Exception | Parity Status | Notes |
|---|---|---|---|---|
| Non-string passphrase | `InvalidPassphrase` / `TypeError` | `InvalidPassphrase` / `TypeError` | aligned | |
| Missing/Uninitialized DB (on open) | `StorageNotInitialized` / `get_status() == "uninitialized"` | `StorageNotInitialized` / `getStatus() == "uninitialized"` | aligned | |
| Uninitialized DB (on operation) | `StorageLocked` | `StorageLocked` | aligned | Operations fail if not unlocked. |
| Database already exists (on init) | `StorageAlreadyInitialized` | `StorageAlreadyInitialized` | aligned | Verified in write-matrix fixtures. |
| Wrong passphrase | `UnlockFailed` | `UnlockFailed` | aligned | |
| Invalid UUID format | `InvalidUuid` | `InvalidUuid` | aligned | Both enforce strict regex. |
| Invalid Content-Type format | `InvalidContentType` | `InvalidContentType` | aligned | Both enforce string, `/`, and no control chars. |
| Invalid payload (functions, cycle) | `InvalidPayload` | `InvalidPayload` | aligned | |
| Missing Object UUID / Not Found | `ObjectNotFound` | `ObjectNotFound` | aligned | On retrieve/update/delete. |
| Unknown Object UUID | `ObjectNotFound` | `ObjectNotFound` | aligned | |
| Unsupported Platform | `UnsupportedPlatform` | `UnsupportedPlatform` | aligned | |
| Malformed Metadata / Pre-V1 | `InvalidStorageFormat` | `InvalidStorageFormat` | aligned | |
| Invalid Feature Flags | `InvalidStorageFormat` | `InvalidStorageFormat` | aligned | Both enforce empty arrays. |
| Crypto/Integrity failure | `IntegrityCheckFailed` / `CryptoOperationFailed` | `IntegrityCheckFailed` / `CryptoOperationFailed` | aligned | |
| General Database Backend Error | `DatabaseBackendError` | `DatabaseBackendError` | aligned | Wraps underlying sqlite3 / better-sqlite3 errors. |

## Shared Conformance Coverage Audit

| Conformance Area | Python | Node.js | Coverage Status | Notes |
|---|---|---|---|---|
| JCS (RFC 8785) canonicalization | Yes (via `jcs` package) | Yes (via `json-canonicalize` package) | expanded-positive-vectors-wired | Both enforce JCS and explicitly consume `rfc8785-basic.json` and `generic-positive-coverage.json`. Vector closure was signed off for baseline-public. |
| AAD construction | Yes | Yes | aligned | Both implement the defined AAD concatenation policy. |
| AES-GCM envelope behavior | Yes | Yes | aligned | Both use 96-bit nonces, 128-bit tags. |
| Argon2id profile | Yes | Yes | aligned | Both use Time=3, Mem=65536 KiB, Parallelism=1, Salt=16. |
| UUID policy | Yes | Yes | aligned | Both strictly enforce RFC4122/RFC9562 variants. |
| Metadata validation | Yes | Yes | aligned | Both validate V1 schema versions and `storage_metadata_tbl`. |
| Content-type validation | Yes | Yes | aligned | |
| SQLite schema/profile | Yes | Yes | aligned | Both apply `PRAGMA foreign_keys = ON`. |
| Cross-language execution evidence | direct-public-api-passed | direct-public-api-passed | aligned | Wrapper contracts executed via runner (write/read/update/delete/not-found-after-delete operations) via direct-public-api mode (and legacy public-entrypoint-test-wrapper mode). |

## Conclusion
The Python and Node.js implementations are semantically well-aligned in their core APIs and error models. Both consistently use the same vocabulary for operations and exceptions.

A sign-off document has been executed at [Python/Node.js Baseline-Public Error Taxonomy Sign-off](python-node-baseline-public-error-taxonomy-signoff.md) concluding that no unmapped error conditions remained. This audit served as the final parity check before achieving the `baseline-public` certification.
