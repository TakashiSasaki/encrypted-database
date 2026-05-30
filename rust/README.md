# Rust Portability Validation Scaffold

This directory contains the Rust portability validation and writer scaffold for Storage Format V1 Stable. It is intended to consume shared conformance vectors and uncover portability issues.

The Rust implementation is strictly a portability validation and writer scaffold; it is **not a full production storage library**. Its incompleteness does not weaken the Storage Format V1 Stable status. Currently, a minimal JCS canonicalizer, an Argon2id KDF test, AES-256-GCM AEAD primitive vector validation, Key-Wrap conformance validation, and Payload vector conformance validation are implemented to satisfy the basic test vectors.

Additionally, a SQLite V1 read-only database unlock/decrypt reader and an experimental database writer scaffold have been added.

**Supported API / capability scope (current scaffold):**
* New SQLite V1 Database Creation and initialization (schema population).
* `passphrase_argon2id` unlock provider setup.
* JSON payload encryption and insertion (`store_payload`).
* In-place payload update (`update_payload`) and payload delete (`delete_payload`) for `encrypted_object_tbl` rows only.
* Self-read roundtripping and cross-read compatibility across Go, Rust, Python, and Node.js readers.
* SQLite backend PRAGMA profile in writer initialization: `foreign_keys = ON` is mandatory. `page_size = 4096` and `auto_vacuum = NONE` are writer-initialization requirements for newly created SQLite V1 files. `journal_mode = WAL` and `synchronous = NORMAL` are recommended operational PRAGMAs for supported file-backed environments. WAL/synchronous failure must not invalidate a Storage Format V1 database. WAL is not a Storage Format V1 conformance invariant.

**NOT supported (out of current scaffold scope):**
* Key rotation, destruction, and decrypt-only migrations.
* Key rewrapping.
* Additional unlock providers.
* Blind indexing.
* Production-ready API maturity guarantees (stability/SLA/backward-compat commitments).

**CI Note:** Write-matrix is integrated as path-filtered automatic `pull_request` and `push` CI, alongside manual `workflow_dispatch`.

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


See also: [`docs/implementation-notes/api-parity-matrix.md`](../docs/implementation-notes/api-parity-matrix.md)
