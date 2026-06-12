# C/C++ JCS UTF-16 Key-Ordering Vector Plan

## Status
Accepted

## Context
RFC 8785 (JSON Canonicalization Scheme) requires strict ordering of object keys. The specification requires sorting keys alphabetically based on their UTF-16 code units. This ordering introduces specific edge cases, particularly when comparing ASCII keys against non-ASCII keys, and when comparing surrogate pairs (e.g., emojis) where the sorting order may depend on how the surrogate code units compare rather than their scalar values or UTF-8 byte representation.

Currently, the C and C++ generic JCS implementations are still pending, and the repository relies on a generated-AST scaffold for a subset of basic JCS vectors.

The current `future-boundary-plan.json` file contains `utf16-surrogate-key-ordering` as a planning-only vector. This vector is not consumed by the generated-AST scaffold or any strictly typed active-vector harness.

The goal of this document is to define the plan for UTF-16 key-ordering vectors, separating their active use from their future conformance requirements. UTF-16 key-ordering conformance requires future generic JCS implementation work and must not be treated as covered by the current generated-AST scaffold.

## Current State
- UTF-16 key-ordering vectors (such as `utf16-surrogate-key-ordering`) are strictly **future conformance vectors** and are not currently active generated-AST vectors.
- These vectors reside in `test-vectors/jcs/future-boundary-plan.json`, which is currently **planning-only** and MUST NOT be consumed by current generated-AST scaffolds or active strictly typed runners.
- UTF-16 key-ordering vectors are distinct from parser rejection vectors. They require successful parsing and sorting of valid inputs, whereas rejection vectors require rejecting invalid inputs or generic bounds (like unsafe integers).
- The current C/C++ generated-AST scaffolds **must not be used to claim full RFC 8785 key-ordering coverage**.
- Active positive vectors in `rfc8785-basic.json` will remain limited to fixture-compatible cases unless a later decision safely expands them.

## Future Vector Categories
Future UTF-16 key-ordering vectors will be classified into the following categories:

1. **BMP Non-ASCII Key Ordering:** Keys within the Basic Multilingual Plane (BMP) but outside the ASCII range.
2. **Surrogate-Pair-Sensitive Key Ordering:** Keys containing characters outside the BMP, represented as surrogate pairs in UTF-16, where sorting behavior depends on the surrogate code units rather than Unicode scalar values.
3. **Escaped versus Unescaped Equivalent Key Representation:** Ensuring keys sort identically regardless of whether they were originally escaped in the JSON text or not.
4. **Mixed ASCII / Non-ASCII Key Ordering:** Mixed sets of standard ASCII keys and higher code-point keys.
5. **Unicode Preservation without Normalization:** Ensuring that no implicit Unicode normalization (e.g., NFC/NFD) happens before sorting.
6. **Parser Support Requirements:** Identifying which cases require raw JSON parser support to correctly ingest versus cases that can be represented as parsed values in a parser-free model.

## Activation Conditions
Before UTF-16 key-ordering vectors can become active conformance vectors, the following conditions must be met:

- Explicit expected canonical strings and hex values must be defined for each vector.
- The expected outputs must be verified against Python and Node.js baseline implementations.
- A decision must be made on whether the vector belongs in active positive vectors (`rfc8785-basic.json`), a separate future conformance file, or a generic JCS-only suite.
- It must be confirmed that Go, Rust, and Zig strict loaders are not broken by the addition.
- It must be confirmed that C/C++ generated-AST fixture constraints are respected or explicitly bypassed intentionally by a future generic harness.
- No new metadata fields (like `future_only` or `expected_error`) can be added to the active `rfc8785-basic.json` file to bypass constraints.

## Explicit Non-Goals
This document strictly makes a decision on planning. It does **not** implement:
- Generic JCS serializer.
- UTF-16 key sorting algorithm.
- Raw JSON parser or generic internal value model structs.
- Rejection-vector harness runtime.

## Implementation Planning

The future generic JCS implementation requires strict lexicographical sorting of object keys based on their UTF-16 code units. This section defines a concrete, language-neutral strategy for future C and C++ implementations.

### General Comparator Strategy

The comparator must compare object keys by their UTF-16 code units derived from the already parsed model string value.

It **must not** compare:
- UTF-8 bytes;
- Unicode scalar values directly;
- locale-aware collation order;
- normalized Unicode forms;
- original JSON source spelling.

The intended conceptual flow is:
`UTF-8 model string -> Unicode code point stream -> UTF-16 code unit stream -> lexicographic code-unit comparison`

- For BMP code points, emit one UTF-16 code unit.
- For non-BMP code points, emit a surrogate pair and compare those surrogate code units in order.
- No Unicode normalization should be performed.
- Escaped and unescaped source spellings are equivalent after parsing and must compare by the parsed string value, not by the original JSON text. Raw JSON spelling differences require a future raw parser or generic parser layer and are not solved by parser-free model comparison alone.

### Invalid Input Behavior

- Future implementations must **fail closed** on invalid UTF-8 or invalid Unicode input.
- Embedded NUL (`\u0000`) remains unsupported by the current parser-free models unless a later representation decision explicitly changes that.

### C Implementation Strategy

The C comparator implementation should follow these guidelines:
- **Preferred:** An internal UTF-8-to-UTF-16 code-unit iterator/comparator that can compare incrementally without allocating full temporary UTF-16 buffers.
- **Acceptable fallback:** Temporary internal UTF-16 code-unit buffers with explicit allocation-failure handling if incremental decoding makes the implementation too fragile.
- Invalid UTF-8 must return a non-OK internal model/serialization error.
- The implementation likely belongs as a private helper in `c/src/vault_jcs_model.c` or a narrowly named internal module if the helper grows too large.
- No dependency on ICU or other external Unicode libraries is allowed.
- The existing parser-free model public/internal boundary must be preserved, avoiding accidental changes to the generated-AST scaffolds.

### C++ Implementation Strategy

The C++ comparator implementation must conceptually match the C behavior but remain completely independent:
- **Independence:** C++ must remain independent from the C implementation. It must not call the C comparator or include C parser-free model headers.
- **Platform independence:** Do not rely on platform-dependent `wchar_t`, locale collation, `std::wstring_convert`, or deprecated/implementation-dependent `codecvt` behavior.
- **Implementation:** A future implementation may use a small custom UTF-8 decoder / UTF-16 code-unit iterator, or allocate temporary `std::vector<uint16_t>` buffers if that is simpler.
- **Error handling:** Invalid UTF-8 must fail closed and be handled through the existing `Result<T>` and `ModelError` pattern.
- This must interact safely with existing `std::string` storage and embedded-NUL rejection policies.

### Test and Vector Activation Strategy

UTF-16 key-ordering vectors remain planning-only and are not activated in this stride.

- `future-boundary-plan.json` remains strictly planning-only and must not be consumed by current C/C++ bridge tests.
- The existing `utf16-surrogate-key-ordering` case remains classified as `"future_only": true`.
- Before activation, explicit `expected_string` and `expected_hex` must be defined for each new vector.
- Expected outputs must be verified against Python and Node.js baseline implementations.
- A future decision will determine whether these vectors belong in active `rfc8785-basic.json`, a separate UTF-16 conformance file, or a generic JCS-only suite.
- Go, Rust, and Zig strict loaders must not be broken by the activation of these vectors.
- The generated-AST fixture constraints must be compatible or explicitly handled by a future generic harness.
- No new metadata fields (e.g., `category` or `scope`) should be added to `rfc8785-basic.json` to bypass current constraints.
