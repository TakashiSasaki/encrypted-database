# Rust Portability Validation Scaffold

This directory is currently a portability-validation scaffold. It is intended to consume shared conformance vectors and uncover portability issues before full read/write implementations are developed.

The Rust implementation is not a full, production-ready library. Currently, a minimal JCS canonicalizer, an Argon2id KDF test, AES-256-GCM AEAD primitive vector validation, Key-Wrap conformance validation, and Payload vector conformance validation are implemented to satisfy the basic test vectors. Additionally, a SQLite V1 read-only metadata validator has been added to verify `PRAGMA` headers and logical metadata. Full storage database features, including database unlock/decrypt reader, writer functionality, and cross-language roundtrip testing, remain future tasks.

## Testing

Run tests against the shared conformance vectors:

```bash
cd rust
cargo test
```

You can optionally override the test vectors directory:
```bash
VAULT_TEST_VECTORS_DIR=/path/to/vectors cargo test
```
