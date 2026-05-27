# Go Portability Validation Scaffold

This directory is currently a portability-validation scaffold. It is intended to consume shared conformance vectors and uncover portability issues before full read/write implementations are developed.

The Go implementation is not a full, production-ready library. Currently, a minimal JCS canonicalizer, an Argon2id KDF test, AES-256-GCM AEAD primitive vector validation, Key-Wrap conformance validation, and Payload vector conformance validation are implemented to satisfy the basic test vectors.

Additionally, a SQLite V1 read-only database unlock/decrypt reader and an experimental database writer scaffold have been added.

**What is supported in the minimal writer scaffold:**
* New SQLite V1 Database Creation and initialization (schema population).
* `passphrase_argon2id` unlock provider setup.
* JSON payload encryption and insertion (`StorePayload`).
* Self-read roundtripping and cross-read compatibility across Go, Rust, Python, and Node.js readers.

**What is NOT supported yet:**
* Update/Delete APIs for encrypted objects.
* Key rotation, destruction, and decrypt-only migrations.
* Key rewrapping.
* Additional unlock providers.
* Blind indexing.
* Production-ready public API guarantees.
* Write-matrix automated CI integration (currently exists as a local/manual test harness and a manual `workflow_dispatch` workflow only, not automatically run on push/PR).

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
