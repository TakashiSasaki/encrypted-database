# C Bootstrap Scaffold

This directory contains the initial C bootstrap scaffold for the Encrypted Database project.

## Status

**This is strictly a bootstrap scaffold. It is not a production storage library.**
It does not currently implement Storage Format V1 cryptography, SQLite V1 reading/writing, Argon2id, generic JCS, or matrix integration. It provides partial AAD shared-vector conformance, internal JSON escaping for AAD construction, a limited internal generated-AST JCS basic-vector serializer scaffold, internal UUID syntax validation, and internal content-type boundary validation through internal scaffold helpers. Public API parity is not yet promised.

For a detailed breakdown of planned future steps, see the [C/C++ Native Conformance Roadmap](../docs/implementation-notes/c-cpp-native-conformance-roadmap.md).

## Completed

- Bootstrap build/test scaffold with CMake
- Smoke CLI and library entrypoints
- Partial AAD shared-vector conformance
- Internal JSON escaping for AAD construction
- Limited internal generated-AST JCS basic-vector serializer scaffold
- Internal UUID syntax validation scaffold
- Internal content-type boundary validation scaffold
- C parser-free JCS internal model scaffold

## Missing

- Generic JCS implementation
- Argon2id
- AES-256-GCM
- Key-wrap cryptography
- Payload encryption
- SQLite V1 read-only validation
- SQLite writing
- Read-only matrix
- Write-matrix
- Production public API

## Testing

You can run the smoke tests locally using CMake:

```bash
cd c
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```
