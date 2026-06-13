# C/C++ Generic JCS Implementation Boundary Review

## Status
Accepted

## Purpose
This document provides a boundary review for the C and C++ Generic JCS implementations. It defines what "Generic JCS implementation" means for this repository, clarifies the current state of implementation, sets boundaries for the next development stride, and enumerates the remaining gaps that must be closed before the implementation is considered complete.

## Generic JCS Implementation Scope
For this repository, "Generic JCS implementation" means a fully compliant implementation of the JSON Canonicalization Scheme (RFC 8785) in both C and C++. This implies:
- Loading raw JSON text dynamically at runtime.
- Producing a correct JCS canonical string representation.
- Correctly parsing arbitrary JSON valid according to RFC 8785.
- Correctly failing closed when encountering rejection boundaries (e.g., duplicate keys, embedded NULs in object keys, unsafe/float numbers).
- Handling valid non-ASCII UTF-8 and correct UTF-16 surrogate ordering for object keys.

This is the long-term definition of a complete Generic JCS implementation. It is not the scope of the next implementation stride.

Currently, the C and C++ implementations are **parser-free test-harness scaffolds**. They serialize internal models to JCS output strings but intentionally lack raw JSON text parsing, file loading, and rejection capability. The next stride remains parser-free and limited to serializer/model semantic hardening.

C and C++ are **independent implementations**. C++ code does not and must not wrap, call, or rely on C runtime logic, models, comparators, serializers, or test helpers.

## Boundary Review Checklist
The following sections (Current Layers and Status, and Semantic Gap Audit) collectively serve as the boundary review checklist.

## Current Layers and Status

| Layer | Name | Status | Files Involved | Scope Type | Mutable in Next Stride? | Deferred? |
| --- | --- | --- | --- | --- | --- | --- |
| **Layer A** | Generated-AST bridge tests | Active | `c/src/vault_jcs_internal.h`, `c/tests/test_jcs.c`, `cpp/tests/test_jcs.cpp` | Test-only | No | No |
| **Layer B** | Parser-free in-memory model | Active | `c/src/vault_jcs_model.[ch]`, `cpp/src/vault_jcs_model.[hpp/cpp]` | Candidate | Yes | No |
| **Layer C** | Parser-free model serializer | Active | `c/src/vault_jcs_model.c`, `cpp/src/vault_jcs_model.cpp` | Candidate | Yes | No |
| **Layer D** | Test-only generic positive loader | Active | `c/tests/test_jcs_positive_vector_loader.c`, `cpp/tests/test_jcs_positive_vector_loader.cpp` | Test-only | Yes | No |
| **Layer E** | Build-time generated positive fixture wiring | Active | `scripts/generate_jcs_positive_loader_fixtures.py`, `CMakeLists.txt` | Test-only | Yes | No |
| **Layer F** | Future raw JSON parser / runtime JSON loader | None | N/A | Candidate | No | Yes |
| **Layer G** | Future public C/C++ JCS API | None | N/A | Candidate | No | Yes |

*Note: The generated-AST bridge tests and the generated positive fixture path both serve as mechanisms to seed the internal parser-free models from known test vectors without requiring runtime parsing.*

## Semantic Gap Audit

The following table audits the current C and C++ parser-free model serializers against intended JCS semantics exercised by the vectors:

| Semantic Feature | Status | Notes |
| --- | --- | --- |
| Null serialization | `covered-by-tests` | Supported natively in C/C++ models. |
| Boolean serialization | `covered-by-tests` | Supported natively in C/C++ models. |
| Safe integer serialization | `covered-by-tests` | Handled as safe 64-bit signed integers; floating point unsupported. |
| Safe integer min/max | `covered-by-tests` | `[-9007199254740991, 9007199254740991]` tested via `generic-positive-coverage.json`. |
| Unsupported floats | `deferred-parser-boundary` | Floating-point validation is deferred to the future JSON parser. |
| String escaping | `covered-by-tests` | Quotes, backslashes are escaped correctly. |
| Control character escaping | `covered-by-tests` | Handled properly via serializers with deep semantic coverage. |
| Solidus handling | `covered-by-tests` | Escaping solidus is explicitly prohibited by JCS; verified by vectors. |
| UTF-8 handling | `covered-by-tests` | Natively preserved through string buffers. |
| Embedded NUL rejection boundary | `deferred-parser-boundary` | Deferred until parser strings include explicit lengths. Currently models assume null-terminated strings. |
| Invalid UTF-8 boundary | `implemented-but-needs-more-tests` | Object-key invalid UTF-8 is covered; string-value invalid UTF-8 needs explicit coverage. |
| Object key ordering by UTF-16 code units | `covered-by-tests` | Covered by `utf16-key-ordering.json` logic mapping via surrogate checks. |
| Array recursion | `covered-by-tests` | Tested with `mixed-type-arrays` and `deep-nesting`. |
| Object recursion | `covered-by-tests` | Tested with `nested-objects` and `deeply-nested-object`. |
| Empty string | `covered-by-tests` | Works fine natively in serializers. |
| Empty object key | `covered-by-tests` | Handled via `object-empty-key`. |
| Duplicate-key boundary | `deferred-parser-boundary` | Parser-free models cannot reliably model this as they require parsing to detect duplicates. |
| Raw JSON spelling equivalence | `deferred-parser-boundary` | Extraneous whitespace or exact JSON encoding artifacts depend on the future parser. |
| Parser-dependent concerns | `deferred-parser-boundary` | Handled in Layer F implementation stride. |

## Next Implementation Stride

Based on the audit above, the C and C++ serialization implementations are quite strong, covering almost all of the JCS model semantics.

**Recommended next stride:** `Cross-language read/write compatibility matrix baseline`

### Scope
Improve semantic validation within the existing parser-free internal model layers (Layer B, Layer C, and Layer D). This can involve hardening control-character escaping within the tests or model representations to verify complete safety without altering architectural design.

### Non-Goals
- Raw JSON parsing or parser implementation.
- Runtime JSON text loading from the filesystem.
- Duplicate-key logic implementation.
- Handling rejection boundary vectors (`test-vectors/jcs/future-boundary-plan.json`).
- Public API creation, matrices, writer functionalities, SQLite integration, or cryptographic work.
- Third-party dependency additions.

### Candidate Files
- `c/src/vault_jcs_model.c`
- `cpp/src/vault_jcs_model.cpp`
- `c/tests/test_jcs_model_serialize.c`
- `cpp/tests/test_jcs_model_serialize.cpp`

### Test Vectors
Rely on the existing wired tranches:
- `test-vectors/jcs/rfc8785-basic.json`
- `test-vectors/jcs/utf16-key-ordering.json`
- `test-vectors/jcs/generic-positive-coverage.json`

### Acceptance Criteria
- C/C++ parser-free logic completes string escaping/control character semantic tests with alignment with RFC 8785 semantics within the existing parser-free safe model domain.
- Existing tests and vectors pass without regression.
- C and C++ remain strictly independent implementations.
- No raw parser or file loading mechanics are introduced.

### Risks
- Minor bugs discovered in specific control character edge cases could require complex escaping logic refactoring.
- Enforcing semantic strictness might accidentally trigger behavior that appears parser-dependent.

### Required Test Commands
```bash
cd c && cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure
cd ../cpp && cmake -S . -B build && cmake --build build && ctest --test-dir build --output-on-failure
python scripts/test_generate_jcs_positive_loader_fixtures.py
```
