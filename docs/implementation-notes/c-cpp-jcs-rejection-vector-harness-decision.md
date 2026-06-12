# C/C++ JCS Rejection-Vector Harness Decision

## Status
Accepted

## Context
Storage Format V1 defines rigorous JSON Canonicalization Scheme (RFC 8785) constraints. Currently, the C and C++ native conformance implementations serve as a bootstrap scaffold. They contain a limited generated-AST JCS basic-vector serializer scaffold and are not full, generic JCS implementations.

We currently store edge-case and boundary vectors meant for future use in `test-vectors/jcs/future-boundary-plan.json`. This file is planning-only and explicitly must not be consumed by the current generated-AST scaffold or any strict typed active-vector harnesses.

The goal of this document is to explicitly classify these future boundary and rejection vectors. This determines how they will be consumed when the respective generic implementation stages are reached, without implementing those harnesses now.

## Staged Approach for Future Vectors

The future consumption of `future-boundary-plan.json` will be staged to align with the generic JCS implementation plan:

### 1. Parser-Free Internal-Model Rejection Harness
The first step toward a generic JCS implementation is a parser-free generic serializer. This internal model will accept programmatic values but will lack a raw text parser. Vectors in this category test the boundary of the internal value model (e.g., rejecting out-of-bounds numbers).

Current vectors classified here:
- `unsafe-integer-max-plus-one`: Future parser-free internal-model rejection harness.
- `unsafe-integer-min-minus-one`: Future parser-free internal-model rejection harness.
- `embedded-nul`: Future parser-free internal-model rejection harness, blocked by length-aware string ownership / serialization decision.

### 2. Raw JSON Parser Rejection Harness
A subsequent step is introducing raw text parsing capabilities. Vectors in this category will test parsing boundaries, invalid raw JSON text, and error handling for duplicate keys.

Current vectors classified here:
- `duplicate-keys`: Future raw JSON parser rejection harness.
- `invalid-json-trailing-comma`: Future raw JSON parser rejection harness.

### 3. UTF-16 Key-Ordering Conformance Vector Set
This is not strictly a rejection harness, but a conformance test for edge-case ordering of non-ASCII keys based on surrogate-pair handling, required by RFC 8785.

Current vectors classified here:
- `utf16-surrogate-key-ordering`: Future UTF-16 key-ordering conformance vector set / planning category (not a parser rejection vector).

## Future Harness Schema Rules
Future rejection vectors will not share the strict active positive-vector schema found in `rfc8785-basic.json`.
- `expected_error` values (like `"unsafe_integer"`) are strictly planning-level identifiers until a proper runtime error taxonomy is implemented.
- `input_raw_json` is reserved strictly for the raw JSON parser boundary and must not be used as input for the generated-AST test runner.

## Explicit Non-Goals
This document strictly makes a decision on classification and the staged future harness approach. This decision does **not** implement:
- generic JCS
- raw JSON parser
- parser-free internal-model runtime
- rejection-vector harness runtime
- public JCS API
- provider_config validation
- metadata table validation
- unsafe integer rejection runtime
- duplicate-key parser behavior
- embedded NUL support
- UTF-16 surrogate sorting implementation
- crypto (Argon2id, AES-GCM, key wrapping, payload encryption)
- SQLite (read-only validator, writer)
- matrix integration (read-only, write-matrix)
- production C/C++ APIs
- C++ wrapper over C
- shared C/C++ runtime core
