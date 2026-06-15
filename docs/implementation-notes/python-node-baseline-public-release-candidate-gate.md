# Python/Node.js Baseline-Public Release-Candidate Gate

## Purpose and Scope
This document serves as the final release-candidate evidence gate for the promotion of the Python and Node.js implementations to `baseline-public`. It serves as an auditable checklist tracking the required stability, testing, and alignment for Storage Format V1 capabilities.

## Status: NOT YET BASELINE-PUBLIC
**Python and Node.js are currently `baseline-candidate` / `preview-library` implementations.**
They have passed the public-entrypoint test-wrapper matrix but have not yet received final release certification.

## Storage Format V1 Stable Relationship
Storage Format V1 is Stable. No bytes-on-disk semantic changes, cryptographic adjustments, or schema modifications will be introduced. This document strictly concerns the readiness of the Python and Node.js client libraries to faithfully read and write this stable format.

## Current Evidence Table

| Evidence Category | Status | Details |
|---|---|---|
| Package-root public entrypoints | **Achieved** | `from encrypted_storage import EncryptedStorage` (Python), `const { EncryptedStorage } = require('encrypted-storage')` (Node.js). |
| Cross-language read/write matrix | **Achieved** | Write/read/update/delete/not-found-after-delete matrix passes between Python and Node.js via public-entrypoint test wrappers (`public-entrypoint-passed`). |
| Wrapper status vs Certification | **Clear** | Runner mode is `public-entrypoint-test-wrapper`, certification status remains `public_quality_certification: false`. |
| Shared vector evidence | **Partial** | JCS, AAD, AES-GCM, and Argon2id shared positive vectors are wired and pass. Full shared UUID vector integration is pending. |
| Metadata/version provenance | **Achieved** | `created_by_version` populates accurately. Placeholders removed. |
| README / Package metadata | **Achieved** | Docs are clean, accurate, and do not overclaim status. |
| CI/path-filtered status | **Achieved** | Pipeline executes accurately. |
| API freeze candidate | **Proposed** | Candidate methods/errors exist. Final freeze confirmation pending. |
| Security notes | **Reviewed** | Explicit lack of hard memory zeroization documented. |
| Remaining release blockers | **Pending** | Full shared UUID vector integration, final API freeze review, security sign-off, and removal of public-entrypoint test-wrapper gate. |

## Release-Candidate Checklist
The following items must be verified before proceeding to a final certification PR. This checklist does not imply certification is complete.

- [ ] Confirm public API freeze candidate for Python and Node.js.
- [ ] Confirm public error taxonomy and cross-language error mapping.
- [ ] Confirm public-entrypoint matrix passes for Python -> Python, Python -> Node.js, Node.js -> Python, Node.js -> Node.js.
- [ ] Confirm evidence includes write/read/update/delete/not-found-after-delete.
- [ ] Confirm `public_quality_certification` remains false until final certification.
- [ ] Confirm shared vector coverage status and list any remaining vector gaps.
- [ ] Confirm security notes have been reviewed and sign-off status is explicit.
- [ ] Confirm README/package metadata are release-candidate ready.
- [ ] Confirm no baseline-public wording remains outside a future certification PR.
- [ ] Confirm no Storage Format V1 semantic changes were made.

## Certification PR Requirements
A future final certification PR must show:
- All checklist items above are checked and independently verified.
- The cross-language compatibility runner passing across stable, non-test-wrapper library APIs.
- The removal of `baseline-candidate` / `preview-library` disclaimers from the public READMEs.

## Required Validation Commands
Run the following commands to gather local evidence during the RC phase:

```bash
# Verify stale documentation guardrails
bash scripts/check_stale_docs.sh

# Python validation (using identical interpreter environment as runner)
cd python
python -m pip install -e ".[test]"
pytest
cd ..

# Node.js validation
cd nodejs
npm ci
npm test
cd ..

# Cross-language compatibility matrix runner evidence
python scripts/run_cross_language_compatibility.py --list
python scripts/run_cross_language_compatibility.py --list --json
python scripts/run_cross_language_compatibility.py --execute
python scripts/run_cross_language_compatibility.py --execute --json

# Gated runner unit tests
VAULT_RUN_COMPAT_EXECUTION_TESTS=1 python -m unittest scripts/test_run_cross_language_compatibility.py
```

## Explicit Non-Goals
- Promoting C/C++, Go, Rust, or Zig to production status.
- Adding browser runtime capabilities.
- Changing Storage Format V1 bytes-on-disk semantics.
- Automating PyPI/npm publishing in this stride.

## Remaining Blockers Before Baseline-Public
- Full shared UUID vector integration.
- Final API freeze sign-off.
- Final security notes sign-off.
- Execution matrix transitioned from public-entrypoint test wrappers to direct library integration, proving final public API compatibility.

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

## Security Notes Relationship
Refer to the [Python/Node.js Baseline-Public Candidate Security Notes](python-node-baseline-public-security-notes.md) for explicit boundaries regarding memory zeroization limitations and out-of-scope capabilities.
