# Python/Node.js Baseline-Public Error Taxonomy Sign-off

## Purpose
This document finalizes the error taxonomy and cross-language error mapping for the Python and Node.js storage implementations, establishing them as complete and ready for `baseline-public` certification.

## Error Class Mapping
The following error classes map 1-to-1 between the Python and Node.js implementations:

| Error Case | Error Class | Description |
|---|---|---|
| Invalid Passphrase | `InvalidPassphrase` | Passphrase is not a string or fails validation. |
| Database Not Found/Uninitialized | `StorageNotInitialized` | Attempted to unlock a non-existent or uninitialized DB. |
| DB Locked | `StorageLocked` | Attempted read/write operation without unlocking first. |
| DB Already Initialized | `StorageAlreadyInitialized` | Attempted to initialize an existing, valid database. |
| Bad Passphrase on Unlock | `UnlockFailed` | Authentication tag mismatch during unlock KEK validation. |
| Invalid UUID | `InvalidUuid` | The UUID is not a canonical, lowercase, hyphenated string. |
| Invalid Content-Type | `InvalidContentType` | Content type is malformed, lacks a slash, or has control chars. |
| Invalid Payload | `InvalidPayload` | The payload contains functions, cycles, or fails JCS requirements. |
| Object Not Found | `ObjectNotFound` | Payload UUID does not exist (applies to read/update/delete). |
| Unsupported Platform | `UnsupportedPlatform` | The platform flag is not supported (e.g. `cross_platform` given). |
| Storage Format Error | `InvalidStorageFormat` | Metadata missing, V1 check failed, or feature flags active. |
| Integrity Check Failed | `IntegrityCheckFailed` | The AEAD tag on a row payload is invalid or corrupted. |
| Crypto Error | `CryptoOperationFailed` | A failure inside the lower-level cryptographic routines. |
| Database Backend | `DatabaseBackendError` | A generic error emitted by the SQLite driver. |

## Validation & Coverage Confirmations
- **`ObjectNotFound` on Delete**: Both implementations return `ObjectNotFound` if a delete operation is attempted on a missing UUID. The runner successfully tests this via the `not_found_after_delete` operation using `direct-public-api` execution mode.
- **UUID Validity**: Validated via shared UUID vectors for invalid formats.
- **Payload, Content-Type, Platform, and Passphrase Errors**: Aligned completely across both libraries with no known gaps.
- **Evidence Mode**: `direct-public-api` evidence is the primary execution mode for validation, while `public-entrypoint-test-wrapper` serves as secondary/legacy supporting evidence.

## Sign-off Readiness
No unmapped error conditions or taxonomy blockers remain.
**Status: Ready for reviewer sign-off.**
