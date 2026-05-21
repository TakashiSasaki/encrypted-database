# API Contract and Lifecycle

This document defines the formal public API contract and lifecycle states for the Encrypted Database implementations across Python, Node.js, and browser environments.

## Lifecycle States

The storage implementations must track the database lifecycle using the following conceptual states:

- `uninitialized`: The backend is not yet fully configured or ready. (In browser environments, this is the state before `init()` completes, and before `initializeDatabase` is called).
- `open_locked`: The backend database is initialized or opened, but no active key material is loaded in memory.
- `open_unlocked`: The backend database is initialized and active key material is present in memory, allowing read/write operations.
- `closed`: The backend database connection has been closed and any key material has been cleared. No further operations except state queries are permitted.

When queried via the status API, the implementations will return these states as string values: `"uninitialized"`, `"open_locked"`, `"open_unlocked"`, or `"closed"`.

## Common Core API

The following operations are defined conceptually and must be implemented with idiomatic naming (`snake_case` in Python, `camelCase` in JS/TS).

### `initialize_database` / `initializeDatabase(passphrase, platform)`
- **Precondition**: State must be `open_locked` or `open_unlocked` (if allowing re-initialization of an empty db). Must throw `StorageClosed` if `closed`.
- **Action**: Initializes a new database schema and generates the initial keys using the provided passphrase and platform string. Generating the initial KEK from the passphrase must use the platform-independent Argon2id Profile V1 parameters.
- **Postcondition**: Transitions to `open_unlocked` state. The database is immediately ready for use.
- **Errors**: `StorageAlreadyInitialized`, `StorageClosed`.

### `unlock_database` / `unlockDatabase(passphrase)`
- **Precondition**: State must not be `closed`.
- **Action**: Verifies the passphrase, derives the unlock KEK, unwraps the database KEK, and stores it in memory. If verification fails, any existing active key material is explicitly cleared from memory.
- **Postcondition**: Transitions to `open_unlocked` on success. Transitions to `open_locked` on failure. Remains `uninitialized` if called before the backend is initialized or before any active database KEK metadata exists.
- **Errors**: `StorageClosed`, `StorageNotInitialized`, `UnlockFailed`.

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

## Input Validation

All implementations must strictly validate inputs at the public API boundary before executing backend operations. Relying solely on the SQLite constraints and failing late with generic errors is prohibited.

*   **`schema_uuid` / `object_uuid`**: Must be a string strictly matching the lowercase hyphenated canonical UUID format. Implementations should either automatically normalize non-canonical UUIDs, or throw `InvalidUuid`. The current specification requires rejecting non-canonical inputs (e.g. uppercase, missing hyphens) by throwing `InvalidUuid`. Note that the semantic meaning of the UUID registry is not validated at this boundary.
*   **`content_type`**: Must be a string representing a basic `type/subtype` format. It must not be empty and must not contain control characters. Violations throw `InvalidContentType`. More advanced MIME type parsing may be added in the future.
*   **`payload`**: Must be a plain JSON object (dictionary). Arrays, nulls, primitives, or raw byte buffers are strictly rejected by throwing `InvalidPayload`. This guarantees semantic consistency.
*   **`platform`**: Must be a supported platform identifier string. Violations throw `UnsupportedPlatform`.
*   **`passphrase`**: Must be a string. Empty strings are permitted. If an invalid type is provided, implementations should throw an appropriate stable typed error.

## Error Taxonomy

Implementations must expose specific error types to provide programmatic error handling without parsing message strings.

- `StorageError`: Base error class for all storage errors.
- `InvalidPayload`: The provided payload was not a valid dictionary/object.
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
- **Python**: Expose custom exception classes inheriting from `StorageError`.
- **Node.js/Browser**: Export custom classes extending `Error`. Error handling should rely strictly on custom class instances (`instanceof`) rather than a `.code` property.
