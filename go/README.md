# Go Portability Validation Scaffold

This directory is currently a portability-validation scaffold. It is intended to consume shared conformance vectors and uncover portability issues before full read/write implementations are developed.

The Go implementation is not a full, production-ready library. Currently, a minimal JCS canonicalizer, an Argon2id KDF test, AES-256-GCM AEAD primitive vector validation, Key-Wrap conformance validation, and Payload vector conformance validation are implemented to satisfy the basic test vectors. Additionally, a SQLite V1 read-only metadata validator, a read-only database unlock/decrypt reader, and an experimental database writer scaffold have been added to verify `PRAGMA` headers, logical metadata, database initialization, and basic data insertion/extraction. Full storage database lifecycle features (e.g., update, delete, key rotation), and integration into automated CI cross-language roundtrip testing workflows, remain future tasks.

## Testing

Run tests against the shared conformance vectors:

```bash
cd go
go test ./...
```

You can optionally override the test vectors directory:
```bash
VAULT_TEST_VECTORS_DIR=/path/to/vectors go test ./...
```
