# C Bootstrap Scaffold

This directory contains the initial C bootstrap scaffold for the Encrypted Database project.

## Status

**This is strictly a bootstrap scaffold. It is not a production storage library.**
It does not currently implement Storage Format V1 cryptography, SQLite V1 reading/writing, Argon2id, generic JCS, or matrix integration. It provides partial AAD shared-vector conformance, internal JSON escaping for AAD construction, a limited internal generated-AST JCS basic-vector serializer scaffold, internal UUID syntax validation, and internal content-type boundary validation through internal scaffold helpers. Public API parity is not yet promised.

For a detailed breakdown of planned future steps, see the [C/C++ Native Conformance Roadmap](../docs/implementation-notes/c-cpp-native-conformance-roadmap.md).

## Completed

C and C++ parser-free generated-vector bridges now exist. Both are generated-fixture bridges, not raw parsers or runtime JSON loaders. Both validate active generated vector expected_string and expected_hex. Both remain bootstrap scaffolds. Neither implements full generic JCS. C/C++ parser-free serializers now have hardened UTF-16 key comparator behavior, strictly failing closed on invalid UTF-8 in object keys. A generic positive vector loader design now exists, but no generic loader implementation, raw JSON parser, rejection-vector harness, public C/C++ JCS API, or production integration exists yet. rfc8785-basic.json remains the active generated-AST positive vector suite. utf16-key-ordering.json remains a non-active positive seed. future-boundary-plan.json remains planning-only and must not be consumed by C/C++ test runners. Neither consumes future/rejection vectors. Neither is a production public API.


- Bootstrap build/test scaffold with CMake
- Smoke CLI and library entrypoints
- Partial AAD shared-vector conformance
- Internal JSON escaping for AAD construction
- Limited internal generated-AST JCS basic-vector serializer scaffold
- Internal UUID syntax validation scaffold
- Internal content-type boundary validation scaffold
- C parser-free JCS internal model scaffold
- C parser-free JCS internal model array/object scaffold
- C parser-free JCS internal model serializer seed
- C parser-free JCS model serializer hardening
- C parser-free JCS model serializer vector bridge
- C parser-free JCS model serializer vector bridge expansion
- C/C++ parser-free JCS bridge parity cleanup
- UTF-16 key-ordering positive vector seed

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
