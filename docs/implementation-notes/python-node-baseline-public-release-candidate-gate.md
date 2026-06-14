# Python/Node.js Baseline-Public Release-Candidate Gate

## Purpose and Scope
This document serves as the release-candidate evidence gate for the later promotion of the Python and Node.js implementations to `baseline-public`.
It tracks the evidence of stability, testing, and alignment for Storage Format V1 capabilities.

## Status: NOT YET BASELINE-PUBLIC
**Python and Node.js are currently `baseline-candidate` / `preview-library` implementations.**
They have passed the public-entrypoint test-wrapper matrix but have not yet received final release certification.

## Storage Format V1 Stable Relationship
Storage Format V1 is Stable. No bytes-on-disk semantic changes, cryptographic adjustments, or schema modifications will be introduced. This document strictly concerns the readiness of the Python and Node.js client libraries to faithfully read and write this stable format.

## Current Evidence Table

| Evidence Category | Status | Details |
|---|---|---|
| Package-root public entrypoints | **Achieved** | `from encrypted_storage import EncryptedStorage` (Python), `const { EncryptedStorage } = require('encrypted-storage')` (Node.js). |
| Cross-language read/write matrix | **Achieved** | Write/read/update/delete/not-found-after-delete matrix passes between Python and Node.js via public-entrypoint test wrappers. |
| Shared vector evidence | **Achieved** | JCS, AAD, AES-GCM, Argon2id, and UUID shared positive vectors are wired and pass. |
| Metadata/version provenance | **Achieved** | `created_by_version` populates accurately. Placeholders removed. |
| README / Package metadata | **Achieved** | Docs are clean, accurate, and do not overclaim status. |
| CI/path-filtered status | **Achieved** | Pipeline executes accurately. |
| Remaining release blockers | **Pending** | Final API freeze review, security sign-off, and removal of public-entrypoint test-wrapper gate. |

## Explicit Non-Goals
- Promoting C/C++, Go, Rust, or Zig to production status.
- Adding browser runtime capabilities.
- Changing Storage Format V1 bytes-on-disk semantics.
- Automating PyPI/npm publishing in this stride.

## Promotion Checklist
Before declaring `baseline-public`, the following must be checked:
- [ ] Final sign-off on the API Freeze candidate.
- [ ] Final sign-off on the baseline-public security notes.
- [ ] Stable public API compatibility evidence beyond test-wrapper certification.
- [ ] Removal of all `preview-library` / `baseline-candidate` disclaimers from the public READMEs.

## Evidence Commands to Run Locally
```bash
# Verify unit and core tests
python scripts/run_cross_language_compatibility.py --execute
```

## Do not declare baseline-public until...
Do not declare Python or Node.js as `baseline-public` until the promotion checklist is fully satisfied and a specific release certification pull request is approved and merged.

## API Freeze Candidate Notes
This section documents the current Python and Node.js public API freeze candidate. It is an **API freeze candidate**, not a final API freeze, pending final validation.

### Python Package Import
- `from encrypted_storage import EncryptedStorage`
- Public error classes exposed.
- `__version__` available.

### Node.js Package Import
- `const { EncryptedStorage, errors, ObjectNotFound } = require('encrypted-storage')`
- Local monorepo equivalent `require('.')` / `require('..')` is used appropriately in tests/docs.

### Lifecycle Methods
- `initialize`
- `unlock`
- `lock`
- `close`
- Status methods: `is_closed` / `is_unlocked` (Python), `isClosed` / `isUnlocked` (Node.js).

### Payload Methods
- `store` / `storePayload`
- `retrieve` / `retrievePayload`
- `update` / `updatePayload`
- `delete` / `deletePayload`

### Error Taxonomy Candidate
- `StorageError` base
- `StorageClosed`
- `StorageLocked`
- `StorageNotInitialized`
- `StorageAlreadyInitialized`
- `InvalidStorageFormat`
- `UnlockFailed`
- `ObjectNotFound`
- `UnsupportedPlatform`
- `InvalidUuid`
- `InvalidContentType`
- `InvalidPayload`
- `IntegrityCheckFailed`
- `CryptoOperationFailed`
- `DatabaseBackendError`
- `AadPolicyError`
- `InvalidPassphrase`
