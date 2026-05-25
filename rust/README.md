# Rust Portability Validation Scaffold

This directory is currently a portability-validation scaffold. It is intended to consume shared conformance vectors and uncover portability issues before full read/write implementations are developed.

The Rust implementation is not a full, production-ready library. Currently, a minimal JCS canonicalizer and an Argon2id KDF test are implemented solely to satisfy the basic AAD and KDF test vectors. Full storage database features, including SQLite validation, unlock, decrypt, and writer functionality, are future tasks.

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
