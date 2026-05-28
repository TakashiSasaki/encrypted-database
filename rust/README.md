# Rust Portability Validation Scaffold

This directory is currently a portability-validation scaffold. It is intended to consume shared conformance vectors and uncover portability issues before full read/write implementations are developed.

The Rust implementation is not a full, production-ready library. Currently, a minimal JCS canonicalizer, an Argon2id KDF test, AES-256-GCM AEAD primitive vector validation, Key-Wrap conformance validation, and Payload vector conformance validation are implemented to satisfy the basic test vectors.

Additionally, a SQLite V1 read-only database unlock/decrypt reader and an experimental database writer scaffold have been added.

**Supported API / capability scope (current scaffold):**
* New SQLite V1 Database Creation and initialization (schema population).
* `passphrase_argon2id` unlock provider setup.
* JSON payload encryption and insertion (`store_payload`).
* In-place payload update (`update_payload`) and payload delete (`delete_payload`) for `encrypted_object_tbl` rows only.
* Self-read roundtripping and cross-read compatibility across Go, Rust, Python, and Node.js readers.
* SQLite backend PRAGMA profile in writer initialization: `page_size=4096`, `auto_vacuum=NONE`, `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`.

**NOT supported (out of current scaffold scope):**
* Key rotation, destruction, and decrypt-only migrations.
* Key rewrapping.
* Additional unlock providers.
* Blind indexing.
* Production-ready API maturity guarantees (stability/SLA/backward-compat commitments).
* Write-matrix automated CI integration (currently exists as a local/manual test harness and a manual `workflow_dispatch` workflow only, not automatically run on push/PR).

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
