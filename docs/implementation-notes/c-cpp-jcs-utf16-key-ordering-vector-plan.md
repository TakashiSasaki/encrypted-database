# C/C++ JCS UTF-16 Key-Ordering Vector Plan

## Status
Accepted

## Context
RFC 8785 (JSON Canonicalization Scheme) requires strict ordering of object keys. The specification requires sorting keys alphabetically based on their UTF-16 code units. This ordering introduces specific edge cases, particularly when comparing ASCII keys against non-ASCII keys, and when comparing surrogate pairs (e.g., emojis) where the sorting order may depend on how the surrogate code units compare rather than their scalar values or UTF-8 byte representation.

Currently, the C and C++ generic JCS implementations are still pending, and the repository relies on a generated-AST scaffold for a subset of basic JCS vectors.

The current `future-boundary-plan.json` file contains `utf16-surrogate-key-ordering` as a planning-only vector. This vector is not consumed by the generated-AST scaffold or any strictly typed active-vector harness.

The goal of this document is to define the plan for UTF-16 key-ordering vectors, separating their active use from their future conformance requirements.

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
