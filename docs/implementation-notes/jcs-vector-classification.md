# JCS Vector Classification

## Purpose

This document classifies the JSON Canonicalization Scheme (RFC 8785) vectors used in this repository to validate canonicalization behavior across implementations.

This classification serves as a preparation step for future C and C++ generic JCS implementation work. The current C and C++ generated-AST scaffold can consume only supported fixture types and is not a generic parser. As such, these vectors are carefully curated to test what is currently safe and implemented in baseline systems without introducing breakage.

## Current Vector Files

The primary JCS vector file is `test-vectors/jcs/rfc8785-basic.json`.

This file currently covers basic JSON canonicalization aspects that are safe for all current baseline and scaffold implementations:
- Empty objects and arrays
- Object key ordering (ASCII-based)
- Nested objects and arrays
- Basic and Unicode strings
- Required JSON string escaping
- Signed 64-bit integers

Each vector in this file MUST include the following fields:
- `name`: A stable, descriptive identifier.
- `description`: A short explanation of what the vector tests.
- `input`: The JSON value to be canonicalized.
- `expected_string`: The exact expected JCS canonical string.
- `expected_hex`: The exact expected lowercase hex encoding of the canonical string.

Note: No additional metadata fields (e.g., `category`, `scope`) are added directly to the JSON file to preserve compatibility with existing strictly-typed consumers (e.g., Rust and Go structs). All classification and metadata should be managed within this documentation.

## Suggested Categories

Vectors can be conceptually grouped into the following categories:

- `basic-empty`: Empty objects and arrays.
- `object-key-ordering`: Sorting of keys, particularly ASCII.
- `nested-structures`: Depth and recursive processing.
- `string-escaping`: Handling of control characters, quotes, and backslashes.
- `unicode-preservation`: Ensuring valid UTF-8 sequences are unmodified.
- `integer`: Handling of standard 64-bit signed integers, including zero and negative values.
- `array`: Correct formatting of lists.
- `boolean-null`: Handling of `true`, `false`, and `null`.
- `utf16-key-ordering`: Surrogate-pair sensitive and non-ASCII ordering.
- `number-policy`: Floats, decimals, exponent notation, and negative zero.
- `unsupported-or-future`: Arbitrary precision numbers and specific edge cases.
- `invalid-json-or-parser-boundary`: Duplicate keys, comments, trailing commas, and malformed inputs.

## Coverage Policy

The following categories are currently safe to include in the generated-AST scaffold and the `rfc8785-basic.json` file:
- objects (with basic string keys)
- arrays
- strings (focusing on ASCII and simple Unicode without normalization needs)
- signed 64-bit integers
- booleans
- null

The following categories should remain documentation-only or deferred to future vector sets until parser and generic JCS decisions are explicitly made, as they will break the current generated-AST scaffold or are undefined in the current specification bounds:
- floats / decimals
- exponent notation
- negative zero (`-0`) as a numeric type
- integer ranges exceeding IEEE-754 exact precision limits (Note: The future internal model safe range is defined in [C/C++ JCS Internal Value Model Decision](./c-cpp-jcs-internal-value-model-decision.md), but rejection vectors have not yet been added.)
- arbitrary precision numbers outside the signed 64-bit integer range (deferred until number representation policy is decided)
- duplicate object keys (deferred until parser behavior is decided)
- invalid raw JSON text (deferred until parser behavior is decided)
- raw JSON parser error behavior and limits (deferred until parser behavior is decided, see [C/C++ JCS Parser and Dependency Decision](./c-cpp-jcs-parser-dependency-decision.md))

## C/C++ Applicability

The current C and C++ generated-AST JCS tests should only consume vectors that fit the fixture contract (which currently forbids floats and arbitrary precision).

- Unsupported or future vectors MUST NOT be forced into the C/C++ generated-AST harness yet.
- The `rfc8785-basic.json` file remains restricted to supported fixture-compatible values.
- The fail-closed behavior of the C/C++ generator for unsupported types must not be weakened.
- Do not add a JSON parser to the scaffolds.

## Boundary-Vector Plan

Before proceeding with a future generic JCS implementation in C/C++, the following boundary vectors must be added and classified. This planning ensures that the implementation boundary is unambiguous.

### Required Future Vector Groups:

- **Safe Integer Accepted Vectors:** Values strictly within the IEEE-754 safe integer range.
- **Unsafe Integer Rejection Vectors:** Values outside the safe integer range that must fail closed in the generic model.
- **String Escaping and Control-Character Vectors:** Exhaustive tests for JSON escaping rules (including ASCII control bytes < 0x20, DEL 0x7f, backslash, quotes, etc).
- **UTF-16 Object-Key Ordering Vectors:** Vectors that specifically test non-ASCII keys and surrogate-pair sensitive ordering as per RFC 8785.
- **Duplicate-Key Boundary Vectors:** Vectors explicitly verifying rejection or safe handling of duplicate keys.
- **Embedded NUL Future/Unsupported Vectors:** Vectors testing `\u0000` handling (either failing safely or succeeding if/when length-aware strings are supported).
- **Generated-AST-Runnable vs. Future-Generic-Only:** Explicit separation and metadata documenting which vectors are safe for the current limited generated-AST scaffold, versus vectors strictly intended for testing the future raw JSON parser or generic model.

## Future Expansion Plan

Future strides will introduce separate vector files or structured metadata for:
- RFC 8785 official/reference vectors (if sourced and license-compatible).
- Repository-specific UTF-16 sort edge cases (surrogate pairs and non-ASCII sorting).
- Number policy vectors (testing safe integer bounds and rejection policies).
- Invalid input and parser-boundary vectors (testing fail-closed behavior on raw text).
- Provider config and metadata JCS validation vectors.
