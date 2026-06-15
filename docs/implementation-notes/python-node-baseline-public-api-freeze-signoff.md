# Python/Node.js Baseline-Public API Freeze Sign-off

## Purpose and Scope
This document provides evidence and confirmation that the Python and Node.js storage APIs are frozen and semantically aligned. It is a sign-off readiness document, verifying the `baseline-public` API candidate surface without changing the current `baseline-candidate` status of the libraries.

This review applies exclusively to the Python and Node.js implementations.

## Public Import and Metadata Validation
*   **Python**: The main entrypoint is cleanly exposed via `from encrypted_storage import EncryptedStorage`. Public error classes are exposed at the module level. `__version__` is available.
*   **Node.js**: The main entrypoint is cleanly exposed via `const { EncryptedStorage, errors } = require('encrypted-storage')` relying on standard `package.json` entrypoint resolution. Public errors are exported by name.

## Core API Alignment

The following APIs are structurally and semantically aligned. Naming differences (e.g. `snake_case` vs `camelCase`) are recognized as language-specific idioms and are not considered semantic gaps.

### Lifecycle Methods
| Python | Node.js | Description |
|---|---|---|
| `initialize_database` | `initializeDatabase` | Creates and seeds a new encrypted storage file. |
| `unlock_database` | `unlockDatabase` | Unlocks an existing storage file and derives the KEK. |
| `lock` | `lock` | Forgets the active KEK. |
| `close` | `close` | Closes the underlying database connection. |
| `get_status` | `getStatus` | Returns `"uninitialized"`, `"closed"`, `"open_locked"`, or `"open_unlocked"`. |
| `is_closed` | `isClosed` | Convenience check for the "closed" status. |
| `is_unlocked` | `isUnlocked` | Convenience check for the "open_unlocked" status. |

### Payload Methods
| Python | Node.js | Description |
|---|---|---|
| `store_payload` | `storePayload` | Inserts a new payload, returning a generated Object UUID. |
| `retrieve_payload` | `retrievePayload` | Retrieves a payload by its Object UUID. |
| `update_payload` | `updatePayload` | Replaces an existing payload completely. |
| `delete_payload` | `deletePayload` | Deletes an existing payload. |

## Storage Format V1 Guarantee
We confirm that absolutely no Storage Format V1 semantics were changed during this API freeze readiness stride. The bytes-on-disk representation and cryptographic derivations are strictly identical and stable.

## Sign-off Readiness
No API surface blockers found. The API is frozen and semantically complete.
**Status: Signed off for Python/Node.js baseline-public certification.**
