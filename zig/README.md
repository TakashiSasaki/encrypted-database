# Zig Component

Zig now provides a generalized scaffold CLI for reading and decrypting a requested object from an existing SQLite V1 database. Zig also retains selected fixture validation through `read-fixture`. Zig remains scaffold-level and is not a production storage library. Zig does not provide writer support or a public storage API.

## Commands

Run the smoke test (prints `vault zig smoke test ok`):
```bash
zig build run
```

Run unit tests:
```bash
zig build test
```

Validate an existing SQLite V1 database file (metadata/profile only):
```bash
zig build run -- validate <path-to-sqlite-v1-db>
```

Read and decrypt a payload to stdout:
```bash
zig build run -- read <path-to-sqlite-v1-db> <passphrase> <object-uuid>
```

Validate reading and decrypting a selected fixture payload from a SQLite V1 database:
```bash
zig build run -- read-fixture <path-to-sqlite-v1-db> <passphrase> <object-uuid> <expected-hex>
```

Run the shared vector conformance suite:
```bash
zig build vectors
```

## Shared Vector Conformance

Zig implements shared vector validation for the following primitives, validating exact byte-for-byte correctness against existing Python/Node baselines:
* **JCS Canonicalization:** Implemented (for standard test subset).
* **AAD Construction:** Implemented.
* **AEAD AES-256-GCM:** Implemented.
* **KDF Argon2id:** Implemented.
* **Key Wrap:** Implemented.
* **Payload Encryption:** Implemented.
