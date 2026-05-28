# Write Matrix Interoperability Tests

`test_writer_matrix.sh` validates cross-language read compatibility for experimental Go/Rust writers with store/update/delete lifecycle fixtures.

## What is validated
- Fixture writers emit JSON with `object_uuid`, `initial_payload_hex`, `updated_payload_hex`, `deleted`.
- `update_only` fixture mode is used to verify payload B can be read by Go/Rust/Python/Node readers.
- `update_delete` fixture mode is used to verify delete behavior (`NotFound`) for Go/Rust readers.
- Cleanup includes SQLite WAL sidecars (`*.db-wal`, `*.db-shm`).

## Run
```bash
bash integration-tests/write-matrix/test_writer_matrix.sh
```

- The same script is used by a manual GitHub Actions `workflow_dispatch` workflow.
- Write-matrix is not yet promoted to automatic `push` / `pull_request` CI.
