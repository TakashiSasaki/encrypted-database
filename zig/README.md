# Zig Component

Zig currently provides a smoke test and an initial read-only Storage Format V1 validation scaffold. It is not a production storage library and does not provide a public storage API.

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
