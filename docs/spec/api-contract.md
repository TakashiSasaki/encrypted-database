# API Contract and Lifecycle

This document defines the formal public API contract and lifecycle states for the Encrypted Database implementations across Python, Node.js, and browser environments.

## Lifecycle States

The storage implementations must track the database lifecycle using the following conceptual states:

- `uninitialized`: The backend is not yet fully configured or ready. (In browser environments, this is the state before `init()` completes).
- `open_locked`: The backend database is initialized or opened, but no active key material is loaded in memory.
- `open_unlocked`: The backend database is initialized and active key material is present in memory, allowing read/write operations.
- `closed`: The backend database connection has been closed and any key material has been cleared. No further operations except state queries are permitted.

When queried via the status API, the implementations will return these states as string values: `"uninitialized"`, `"open_locked"`, `"open_unlocked"`, or `"closed"`.

## Common Core API

The following operations are defined conceptually and must be implemented with idiomatic naming (`snake_case` in Python, `camelCase` in JS/TS).

### `initialize_database` / `initializeDatabase(passphrase, platform)`
- **Precondition**: State must be `open_locked` or `open_unlocked` (if allowing re-initialization of an empty db). Must throw `StorageClosed` if `closed`.
- **Action**: Initializes a new database schema and generates the initial keys using the provided passphrase and platform string.
- **Postcondition**: Transitions to `open_unlocked` state. The database is immediately ready for use.
- **Errors**: `StorageAlreadyInitialized`, `StorageClosed`.

### `unlock_database` / `unlockDatabase(passphrase)`
- **Precondition**: State must not be `closed`.
- **Action**: Verifies the passphrase, derives the unlock KEK, unwraps the database KEK, and stores it in memory.
- **Postcondition**: Transitions to `open_unlocked`.
- **Errors**: `StorageClosed`, `UnlockFailed`.

### `store_payload` / `storePayload(schemaUuid, contentType, payload)`
- **Precondition**: State must be `open_unlocked`.
- **Action**: Encrypts and stores the payload in the database.
- **Postcondition**: Returns the `objectUuid`.
- **Errors**: `StorageLocked`, `StorageClosed`.

### `retrieve_payload` / `retrievePayload(objectUuid)`
- **Precondition**: State must be `open_unlocked`.
- **Action**: Retrieves, decrypts, and verifies the payload for the given `objectUuid`.
- **Postcondition**: Returns the original JSON payload.
- **Errors**: `StorageLocked`, `StorageClosed`, `ObjectNotFound`, `IntegrityCheckFailed`.

### `lock` / `lock()`
- **Precondition**: None (idempotent).
- **Action**: Clears active key material from memory.
- **Postcondition**: State transitions to `open_locked` if previously `open_unlocked`.
- **Errors**: If called in the `closed` state, throws `StorageClosed`.

### `close` / `close()`
- **Precondition**: None (idempotent).
- **Action**: Clears active key material and closes the underlying backend database connection.
- **Postcondition**: State transitions to `closed`.

### Lifecycle Query APIs
All implementations must expose the following state helpers:
- `is_unlocked()` / `isUnlocked()` -> `boolean`
- `is_closed()` / `isClosed()` -> `boolean`
- `get_status()` / `getStatus()` -> `string` (returns `"uninitialized"`, `"open_locked"`, `"open_unlocked"`, or `"closed"`)

## Error Taxonomy

Implementations must expose specific error types to provide programmatic error handling without parsing message strings.

- `StorageError`: Base error class for all storage errors.
- `StorageClosed`: Action attempted on a closed database.
- `StorageLocked`: Action attempted without an active unlocked KEK.
- `StorageNotInitialized`: Action attempted before the database was initialized.
- `StorageAlreadyInitialized`: Initialization attempted on an already-initialized database.
- `UnlockFailed`: Incorrect passphrase or corrupted KEK wrapping.
- `ObjectNotFound`: The requested UUID does not exist.
- `UnsupportedPlatform`: The provided platform string is unsupported or invalid.
- `InvalidUuid`: A provided UUID was malformed.
- `InvalidContentType`: The provided content type string was invalid.
- `IntegrityCheckFailed`: AEAD authentication tag failed or data was tampered with.
- `CryptoOperationFailed`: An underlying cryptographic operation failed.
- `DatabaseBackendError`: An unhandled exception from the database backend.
- `AadPolicyError`: The specified AAD policy is unknown or mismatched.

### Language-Specific Error Handling
- **Python**: Expose custom exception classes inheriting from `StorageError` or standard exceptions where appropriate (e.g., `ValueError` for generic validation).
- **Node.js/Browser**: Export custom classes extending `Error`, each with a `.code` property that matches the error name (e.g., `err.code === 'StorageLocked'`).
