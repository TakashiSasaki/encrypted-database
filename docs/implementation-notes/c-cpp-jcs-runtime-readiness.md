# C/C++ JCS Runtime Readiness

## Status
Accepted

## Purpose
This document finalizes the documentation, design, and readiness-gate stride for the C/C++ parser-free generic JCS implementation. It answers what is ready for runtime implementation, what remains deferred, and explicitly defines the acceptance criteria and boundaries for the very first runtime implementation slice.

This document serves as the gate between architectural planning and the beginning of C/C++ internal runtime modeling.

## Current State and Policy Summary

*   **Current Scaffold Boundary:** The C and C++ scaffolds rely on a generated-AST fixture contract (`vault_jcs_internal.h`) strictly as an internal test-harness contract for basic vectors. It is not a generic parser and does not implement a full canonicalizer.
*   **Accepted Internal Model Direction:** A parser-free generic internal value model supporting null, boolean, safe-integer, string, array, and string-keyed objects.
*   **Active Positive Vector Policy:** `rfc8785-basic.json` remains the only active positive vector file consumed by generated-AST scaffolds.
*   **Future/Rejection Vector Policy:** `future-boundary-plan.json` remains strictly planning-only and must not be consumed by current harnesses. Rejection vectors are deferred to future parser-free and raw-parser harnesses.
*   **UTF-16 Key-Ordering Policy:** UTF-16 sorting and surrogate key-ordering vectors are future conformance vectors, distinct from current generated-AST capabilities.
*   **C/C++ Independence Policy:** C and C++ remain independent native implementations. C++ must not wrap or depend on the C runtime serializer logic.
*   **No Raw JSON Parser:** The first runtime slice will not introduce a raw JSON text parser.
*   **No Public API:** The first runtime slice will not expose public JCS APIs.
*   **No Integration:** The first runtime slice will not introduce cryptography, SQLite read/write support, or read-only/write-matrix integration.

## Runtime Readiness Checklist

The following prerequisites must be resolved before proceeding with generic JCS implementation. Their current status is classified below:

| Prerequisite | Status | Notes |
| :--- | :--- | :--- |
| Generic JCS strategy decision | `ready` | Option 3 (Hybrid staged approach) accepted. |
| Parser/dependency decision | `ready` | Parser-free internal model accepted first; dependencies rejected. |
| Internal value model decision | `ready` | Defined types and IEEE-754 safe integer bounds. |
| Fixture contract cleanup | `ready` | Clarified as test-harness seed only. |
| Active/future vector separation | `ready` | `rfc8785-basic.json` active; `future-boundary-plan.json` planning. |
| Future/rejection vector harness decision | `ready` | Staged approach defined. |
| UTF-16 key-ordering vector plan | `ready` | Classified as future conformance vectors. |
| C ownership model decision status | `ready-for-first-slice`| Explicit ownership and preliminary error codes expected. |
| C++ ownership model decision status | `ready-for-first-slice`| Standard RAII containers expected. |
| Error taxonomy decision status | `deferred` | Preliminary internal error codes acceptable for the first slice; full taxonomy deferred. |
| Embedded NUL decision status | `blocked` | Needs length-aware string decision; not supported in first slice. |
| Safe integer boundary status | `ready` | IEEE-754 safe integer range. |
| Duplicate-key policy status | `ready` | Rejected from the internal value model / must be impossible by construction. |
| Future raw parser boundary status | `deferred` | Not in scope for initial runtime slice. |

## First Runtime Implementation Slice

**Completed.** The first runtime implementation slice was small and language-specific:

**Target:** `C parser-free JCS internal model scaffold`, `C parser-free JCS internal model serializer seed`, and `hardened generated-vector bridge`

This started the runtime work safely in one language (C) to establish the pattern before replicating or adapting to C++. The model supports null, boolean, safe integer, string (without embedded NUL), array, and object types. A serializer seed exists for these types.

### Scope (Completed)
*   Internal C value type enum (`VaultJcsModelType`), extended with arrays and objects.
*   Internal C value struct skeleton defining the internal nodes (`VaultJcsModelValue`), supporting nested composite types.
*   Construction helpers for `null`, `boolean`, `safe integer`, `string` (without embedded NUL), `array`, and `object` (with duplicate key rejection).
*   Cleanup/free functions for explicit ownership, including recursive deep cleanup.
*   Internal serializer seed (`vault_jcs_model_serialize`) emitting compact JSON, including basic string escaping.
*   Minimal internal-only tests validating construction, deep copies, cleanup, serialization, and a strictly-bounded generated-fixture bridge against active vectors.
*   **Serializer Hardening:** Overflow protection for buffer allocation, memory limits, and explicit null/malformed AST failure safety returning detailed error codes instead of silent crashes.

### Touched Files
*   `c/src/vault_jcs_model.h`
*   `c/src/vault_jcs_model.c`
*   `c/tests/test_jcs_model.c`
*   `c/CMakeLists.txt`

### Acceptance Criteria
1.  **C and C++ Independence:** C and C++ independence remains strictly intact.
2.  **No Public API:** No public JCS API is exposed in the headers.
3.  **No Raw JSON Parser:** No raw JSON text parser is added.
4.  **Not Complete:** The generic serializer is not claimed to be complete.
5.  **No Regressions:** Existing generated-AST tests still pass.
6.  **Vectors Untouched:** Active vectors (`rfc8785-basic.json`) remain unchanged unless explicitly required. `future-boundary-plan.json` remains strictly planning-only.
7.  **No Dependencies:** No third-party dependency, Conan, or vcpkg is introduced.
8.  **No Generated Artifacts:** No generated artifacts or build outputs are committed.

### Explicit Non-Goals
*   Implementation of the full generic JCS serializer completion claim.
*   Implementation of full RFC 8785 UTF-16 key sorting (the seed uses a simple `strcmp` limitation).
*   Raw JSON parser.
*   Rejection-vector runtime harness logic.
*   Public JCS API.
*   C++ implementation.
*   Crypto, SQLite, matrix integration, or production API.

## Error and Ownership Readiness

*   **Error Handling:** The first C runtime slice may use preliminary, internal-only error codes (e.g., for memory allocation failures). Full error taxonomy is deferred. C++ error handling is deferred since the first slice focuses on C.
*   **String Ownership:** Strings require explicit ownership in C. Embedded NUL (`\u0000`) remains unsupported until a length-aware string model is firmly decided.
*   **Integer Safety:** Unsafe integer rejection is a future generic-model requirement, not a generated-AST concern. The new struct must represent the IEEE-754 safe range constraint.
*   **Duplicates:** Duplicate-key rejection is not an immediate concern for the very first slice (which may defer objects entirely), but construction APIs must eventually fail on or prevent duplicates.

## Vector and Test Readiness

*   `rfc8785-basic.json` remains the active positive input for the existing generated-AST scaffold. The first internal model scaffold should use small, dedicated internal C tests rather than attempting to consume all JCS vectors immediately.
*   `future-boundary-plan.json` remains planning-only.
*   UTF-16 key-ordering vectors remain future conformance vectors.
*   Cross-language vector checks remain baseline validation, not proof of C/C++ generic JCS completeness.
