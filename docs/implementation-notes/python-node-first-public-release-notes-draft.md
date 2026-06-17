# Python/Node.js First Public Release Candidate Notes Draft

## Overview
We are preparing for the first public release candidate of the `encrypted_storage` library for Python and Node.js.

Both the Python and Node.js implementations have been certified as **`baseline-public`**, meaning they provide stable, production-ready public APIs for reading and writing to the Encrypted Database.

## Storage Format V1 Stable
This release candidate affirms that **Storage Format V1 is Stable**. There are no changes to the bytes-on-disk semantics, JCS canonical exactness, metadata structures, or security profiles.

## Supported APIs
The following core capabilities are supported in both languages:
- **Lifecycle:** `initializeDatabase` (Node.js) / `initialize_database` (Python), `unlockDatabase` (Node.js) / `unlock_database` (Python), `lock`, `close`, `isClosed` (Node.js) / `is_closed` (Python), `isUnlocked` (Node.js) / `is_unlocked` (Python)
- **Payload Operations:** `storePayload` (Node.js) / `store_payload` (Python), `retrievePayload` (Node.js) / `retrieve_payload` (Python), `updatePayload` (Node.js) / `update_payload` (Python), `deletePayload` (Node.js) / `delete_payload` (Python)

## Quality & Compatibility Evidence
- **Cross-language Compatibility:** A comprehensive read/write matrix guarantees that databases created in Python can be seamlessly read and modified in Node.js, and vice-versa.
- **Installed-Distribution Preflight:** The release artifacts (wheels, sdists, and npm tarballs) have been rigorously tested through clean-install smoke tests and isolated cross-language validation matrices.

## Known Unsupported Features (Non-Goals)
The following advanced features are not supported in this initial release:
- Key rotation, rewrap, and destroy
- Additional unlock providers (only passwords with Argon2id are currently supported)
- Blind indexes
- Browser real-runtime coverage (WebCrypto)
- C/C++ storage APIs (currently bootstrap-scaffolds)
- Go, Rust, and Zig public APIs (currently portability-validation scaffolds)

## Security Boundary
Please note that this release does **not** constitute an external security audit.
Furthermore, exact memory zeroization of sensitive material is runtime-dependent (particularly in Node.js and standard Python) and not strongly guaranteed.

## Future Installation
*(The following commands represent future publication-time installation instructions, not evidence of current publication. Packages are not yet published.)*

**Python:**
```bash
pip install encrypted_storage
```

**Node.js:**
```bash
npm install encrypted-storage
```
