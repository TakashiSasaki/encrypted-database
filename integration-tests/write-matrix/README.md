# Write Matrix Interoperability Tests

This directory contains experimental cross-language interoperability tests validating the newly implemented Go and Rust writer scaffolds.

## Overview
The `test_writer_matrix.sh` script orchestrates roundtrip tests between the Go and Rust experimental writers and their respective read-only readers. It verifies that databases created and populated by one language implementation can be successfully unlocked and the payloads correctly decrypted by another language implementation.

**Note:** This is a local, manual test harness. Go and Rust writer implementations are currently portability scaffolds and do not represent the final production-ready features. As such, these tests are not integrated into the automated CI workflows yet.

## Prerequisites
- Go 1.21+
- Rust (Cargo) 1.70+
- Node.js 18+ (npm installed)
- Python 3.10+ (pip installed)

## Usage
Run the test script directly:
```bash
./test_writer_matrix.sh
```

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
