# C/C++ Generic Positive Vector Loader Design

## Status
Accepted

## Purpose
This document defines the architecture, boundary, and data contracts for the future C and C++ generic positive vector loader.

The generic positive vector loader will be a test-harness mechanism that reads positive generic JSON vector files and programmatically builds C/C++ parser-free internal models for generic canonicalization testing.

## Boundary Definition
**Decision:** The generic positive vector loader is strictly a test-harness layer.

It is **not**:
- a raw JSON text parser;
- a public API;
- a production serializer API;
- a rejection-vector harness;
- a generated-AST fixture generator;
- a replacement for the existing `scripts/generate_jcs_test_vectors.py` generated-AST bridge.

Its sole responsibility is to take already parsed positive vector data (e.g., from an external JSON loader in the test harness or a very strict internal test-loader scaffold) and recursively construct the internal C/C++ parser-free models. It focuses explicitly on **positive** canonicalization testing, separate from invalid JSON text handling or rejection vectors.

## Candidate Vector Sources

The loader's policy toward existing JSON vector files is strictly defined:

1. `test-vectors/jcs/rfc8785-basic.json`
   - **Status:** Active generated-AST positive vector suite.
   - **Policy:** This remains the active suite for the generated-AST scaffold. It is a possible future generic-positive-loader source provided strict compatibility is confirmed. No ad hoc metadata fields are allowed. Do not modify.

2. `test-vectors/jcs/utf16-key-ordering.json`
   - **Status:** Non-active positive vector seed.
   - **Policy:** This is baseline verified via `scripts/verify_jcs_utf16_vectors.py`. It is a strong candidate for future generic positive vector loader tests but remains un-wired for now.

3. `test-vectors/jcs/future-boundary-plan.json`
   - **Status:** Planning-only.
   - **Policy:** This file MUST NOT be consumed by the generic positive vector loader. Some entries test rejection behavior or are raw-parser-dependent, which are explicitly out of scope for the positive loader.

## Supported Schema

The future generic positive vector loader should expect vector objects with the following shape:

```json
{
  "name": "...",
  "description": "...",
  "input": { },
  "expected_string": "...",
  "expected_hex": "..."
}
```

The `"input"` field may contain:
- JSON objects (with valid UTF-8 string keys)
- JSON arrays
- strings (valid UTF-8, no embedded NUL)
- booleans
- null
- integers strictly within the IEEE-754 safe integer range.

The loader must initially reject or skip (fail-closed) any vector containing:
- floating-point numbers;
- numbers outside the IEEE-754 safe integer range;
- raw JSON text fields such as `"input_raw_json"`;
- `"expected_error"`;
- `"future_only"`;
- duplicate-key cases;
- embedded NUL cases;
- invalid JSON cases;
- any metadata fields not explicitly defined by the positive vector schema.

## Number Policy
The C/C++ parser-free internal model currently supports only safe integers `[-9007199254740991, 9007199254740991]`.

The future loader must reject vectors whose parsed `"input"` contains:
- integers outside this range;
- floating-point values;
- exponent notation if it cannot be represented as an already parsed safe integer with exact semantics;
- arbitrary precision values.

## String and UTF-8 Policy
The generic positive vector loader initially accepts only valid UTF-8 strings and object keys, and rejects embedded NUL (`\u0000`).

- Object keys must be valid UTF-8, as C/C++ parser-free serializers use UTF-16 code-unit ordering.
- Invalid UTF-8 string-value handling remains a separate hardening topic for the parser-free serializer/model layer, but loader tests must not silently accept invalid UTF-8 values. Valid UTF-8 only is the intended boundary.
- Escaped versus unescaped source spelling equivalence is raw/parser-dependent and remains future work.

## C/C++ Model Construction Strategy

### For C
The loader should:
- Recursively allocate and initialize `VaultJcsModelValue` structs.
- Use explicit creation helpers: `vault_jcs_model_init_null`, `vault_jcs_model_init_boolean`, `vault_jcs_model_init_integer`, `vault_jcs_model_init_string`, `vault_jcs_model_init_array`, `vault_jcs_model_init_object`.
- Ensure robust cleanup on partial construction failure.
- Map unsupported input shapes or values to deterministic test-loader errors, entirely separate from any future production API errors.

### For C++
The loader should:
- Recursively build `vault::jcs::ModelValue` instances via `make_null`, `make_boolean`, `make_integer`, `make_string`, `make_array`, `make_object`.
- Handle `Result<T>` errors gracefully, failing the specific test vector.
- Maintain complete C++ independence from C (do not call C helpers, do not include C model headers).

## Future Test Harness Shape
The eventual test harness built upon this design will follow this flow:
1. Read a target positive vector file.
2. Validate the positive-vector schema.
3. Traverse the parsed generic JSON and build the internal C or C++ model.
4. Serialize the constructed model using the parser-free serializer.
5. Compare output to `"expected_string"`.
6. Compare UTF-8 hex output to `"expected_hex"`.
7. Free/cleanup all constructed models safely.
8. Fail fast and clearly with the vector name on any mismatch or construction error.

## Implementation Scaffold Status
**Update (Current Stride):** The generic positive vector loader scaffold has been implemented as a test-harness-only mechanism.

- **Independent Implementations:** C and C++ have independent scaffold loader logic in their respective test suites (`c/tests/test_jcs_positive_vector_loader.c` and `cpp/tests/test_jcs_positive_vector_loader.cpp`). The C++ scaffold does not call C helpers or use C model headers.
- **Fail-Closed Behavior:** The loader converts from a test-only generic in-memory representation to the parser-free internal model. Unsupported forms (e.g., floating-point, unsafe integers, embedded NULs, duplicate keys, raw JSON sentinels, rejection metadata) result in deterministic loader errors and test failures, confirming a strict fail-closed boundary.
- **Deferred Work:** The scaffold remains a pure in-memory test construct. It still **does not** parse JSON text, load vector JSON files at runtime, consume `future-boundary-plan.json`, wire `utf16-key-ordering.json` to generated tests, or modify `rfc8785-basic.json`.

## Non-Goals
This design stride explicitly does **not** implement:
- the full runtime generic JSON positive vector loader itself (only the in-memory scaffold is built);
- a raw JSON parser;
- a rejection-vector harness;
- automatic consumption of `future-boundary-plan.json`;
- C/C++ generated bridge integration for `utf16-key-ordering.json`;
- generic JCS completion;
- public C/C++ JCS APIs.
