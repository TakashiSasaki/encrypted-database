# Write Matrix Interoperability Tests

`test_writer_matrix.sh` validates cross-language read compatibility for experimental Go/Rust writers with **store/update/delete** lifecycle fixtures.

## What is validated
- Fixture writers emit JSON with `object_uuid`, `initial_payload_hex`, `updated_payload_hex`, `deleted`.
- Readers (Go/Rust/Python/Node) validate updated payload (`payload B`) after writer update.
- Delete-afterwrite behavior is validated as `NotFound` for **Go/Rust readers only**.
- Cleanup now includes SQLite WAL sidecars (`*.db-wal`, `*.db-shm`).

## Run
```bash
bash integration-tests/write-matrix/test_writer_matrix.sh
```
