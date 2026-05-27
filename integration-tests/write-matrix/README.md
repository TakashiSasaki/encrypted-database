# Write Matrix Interoperability Tests

This directory contains experimental cross-language interoperability tests validating the newly implemented Go and Rust writer scaffolds.

## Overview
The `test_writer_matrix.sh` script orchestrates roundtrip tests between the Go and Rust experimental writers and the Go, Rust, Python, and Node.js readers. It verifies that databases created, updated, and deleted by the Go/Rust writer scaffolds can be successfully unlocked and the payloads correctly decrypted (or NotFound verified) by baseline language implementations. The tests orchestrate `store`, `update`, and `delete` scenarios. Note that `delete` performs a logical hard delete on the payload row without secure erase guarantees or key cleanup.

**Note:** Go and Rust writer implementations are currently portability scaffolds and do not represent final production-ready public APIs (key lifecycle, key rotation, and secure erase are intentionally absent). This test matrix is not yet integrated into automated `push` or `pull_request` CI workflows. It can be run either locally or manually via the GitHub Actions `Write Matrix` workflow using `workflow_dispatch`.

## Prerequisites
- Go 1.21+
- Rust (Cargo) 1.70+
- Node.js 18+ (npm installed)
- Python 3.10+ (pip installed)

## Usage

### Local Execution
Run the test script directly:
```bash
bash integration-tests/write-matrix/test_writer_matrix.sh
```

### Manual CI Execution
Trigger the `Write Matrix` workflow via GitHub Actions using the `workflow_dispatch` event.

*Note: The script will automatically attempt to install the necessary local Python and Node.js dependencies (`pip install -e .[test]` and `npm ci`) before running.*

## Matrix Combinations Supported
- Go Writer -> Go Reader
- Go Writer -> Rust Reader
- Go Writer -> Python Reader
- Go Writer -> Node Reader
- Rust Writer -> Rust Reader
- Rust Writer -> Go Reader
- Rust Writer -> Python Reader
- Rust Writer -> Node Reader
