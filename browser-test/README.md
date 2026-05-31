# Browser/Web Environment Baseline Implementation

This directory contains the baseline `browser-test` implementation of the Storage Format V1 Stable. It validates core Storage Format V1 logic utilizing the browser-compatible `sql.js` for an in-memory SQLite backend.

## Features & Implementation Status
- Manages encryption key hierarchies (`unlock_kek` -> `database_kek` -> `record_dek`).
- Encrypts payloads using AES-256-GCM (currently utilizing a Node.js crypto fallback shim in tests; true WebCrypto fallback is future work).
- Supports full payload lifecycle operations: `storePayload`, `retrievePayload`, `updatePayload`, and `deletePayload`.
- Validates the V1 schema, metadata, and JCS canonical exactness policies.

## SQLite / sql.js Caveats
Because `sql.js` creates a virtual in-memory database and its export/import serialization flow does not reliably persist SQLite PRAGMA properties like `PRAGMA application_id` and `PRAGMA user_version`:
- This implementation bypasses explicit PRAGMA application ID checks and relies entirely on the `storage_metadata_tbl` for database format identity.
- It omits file-backed corruption checking (like explicitly ignoring `CHECK` constraints on disk to test backend error propagation).
- It is currently excluded from the local file-based `write-matrix` cross-language interoperability harness (though it implements and passes the same logical test vectors and constraints as Python and Node.js).

## Installation and Testing
```bash
cd browser-test
npm install
npm test
```

See also: [`docs/implementation-notes/api-parity-matrix.md`](../docs/implementation-notes/api-parity-matrix.md)