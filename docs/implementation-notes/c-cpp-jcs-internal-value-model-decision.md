# C/C++ JCS Internal Value Model Decision

## Status
Accepted

## Context
The C and C++ implementations are independent, native conformance scaffolds. Currently, they feature a limited generated-AST JCS basic-vector serializer scaffold.

- A parser-free generic serializer over an internal value model is the accepted next implementation path.
- C/C++ do not currently have generic JCS.
- C/C++ do not currently have a raw JSON parser.
- C/C++ do not currently expose public JCS APIs.
- The generated-AST fixture contract is an internal test-harness contract, not a runtime storage format, not a public API, and not necessarily the final internal value model.
- C and C++ are independent implementations.
- C++ must not wrap or call C runtime serializer/model logic.
- Shared vectors and documentation define behavioral conformance.

## Decision Scope

This document defines the accepted internal typed value model boundary for a future parser-free generic JCS serializer in C and C++. It covers:
- What value types should the first parser-free generic serializer accept?
- How strings and embedded NULs should be represented internally.
- What integer range is safe for the initial model.
- How unsupported numeric cases should be treated.
- Object boundaries, key ordering, and duplicate key handling.
- C and C++ ownership models.
- Independence of C and C++ implementations.

## Accepted Value Types

The accepted first-stage internal value model supports the following types:
- null
- boolean
- string
- integer
- array
- object with string keys

The first-stage internal value model explicitly **excludes**:
- floats
- decimals
- exponent notation
- negative zero as a distinct numeric concept
- arbitrary precision numbers
- non-string object keys
- duplicate object keys as accepted canonicalization input
- raw JSON text
- parser errors
- provider config schema
- metadata table schema

## String Boundary

- Strings are Unicode scalar values represented as UTF-8 bytes, or as language-specific internal string types whose serialized output is UTF-8.
- No Unicode normalization is performed.
- JSON string escaping is handled by the serializer.
- ASCII control characters are serialized using JSON escape rules.
- The slash `/` character is not escaped.
- Object keys and string values must use the exact same escaping rules.

### Embedded NUL (`\u0000`) Support
Embedded NUL / `\u0000` support remains `needs-decision`.

- The current generated-AST fixture generation rejects embedded NUL due to C string-literal / NUL-terminated string constraints.
- A future runtime/internal value model may need length-aware strings if `\u0000` support is required.
- Supporting `\u0000` has ownership, allocation, escaping, test-vector, and cross-language API implications.
- The first-stage generic value model explicitly does not support embedded NUL until length-aware string ownership and serialization rules are explicitly specified.

## Integer Boundary

When defining the integer boundaries for the internal generic value model, several options exist:

- **Option A:** signed 64-bit integer range. Matches the current generated-AST fixture scaffold, but may exceed cross-language JSON number safety in JavaScript-like environments.
- **Option B:** IEEE-754 safe integer range only. Aligns better with conservative cross-language JSON number interoperability, but is narrower than the current generated-AST scaffold.
- **Option C:** No generic numeric support beyond existing vectors until number-policy vectors are added.

**Decision:** The future parser-free generic internal value model will initially accept only JSON integers within the IEEE-754 safe integer range (Option B). Unsafe integers should fail closed in the future generic model.

The existing generated-AST scaffold’s signed 64-bit behavior remains scaffold-specific and does not define the future generic value model boundary. The generic value model should remain conservative unless a later number-policy stride decides otherwise.

## Unsupported Number Representation

Future unsupported numbers should be handled conceptually as follows:
- Unsupported numbers should fail closed.
- Floats, decimals, and exponent notation should not be accepted by the first-stage internal model.
- Arbitrary precision numbers should not be accepted by the first-stage internal model.
- Negative zero (`-0`) should not be accepted as a distinct number.
- The future raw parser phase must define the parse-time rejection/error taxonomy.

(Note: Do not implement error enums or runtime behavior for this in the current stride.)

## Object Boundary

- Object keys are strings.
- Object values are valid model values.
- Duplicate keys are not accepted in the internal value model.
- If the model is constructed programmatically, construction should either reject duplicate keys or make duplicates impossible by construction.
- The future raw JSON parser phase must separately define duplicate-key behavior.
- The serializer is responsible for ordering keys for canonical output.
- UTF-16 object member sorting remains a future precise implementation requirement.

## C and C++ Ownership Model Planning

Before generic implementation, the following concerns must be addressed:

### C Ownership Model
- **Explicit Ownership:** C must explicitly define whether values take ownership of memory or borrow it.
- **Length-Aware Strings:** If embedded NUL is eventually supported, length-aware string/buffer representations will be required.
- **Allocator Strategy:** Must define allocation, particularly if dynamically growing arrays or strings are used.
- **Error Codes:** Failures must be propagated using explicit error codes or null returns, rather than complex error objects.
- **No C++ Dependency:** C implementation must remain completely decoupled from C++ standard libraries or runtime.

### C++ Ownership Model
- **RAII:** C++ should leverage RAII for memory management of the internal model.
- **Standard Types:** `std::string`, `std::vector`, and `std::string_view` should be used where appropriate.
- **Exception vs Error-Code:** The decision to use exceptions or `std::expected` / error codes must be left explicit or decided prior to implementation.
- **No Wrapper Dependency:** C++ must not be a wrapper around the C runtime serializer/model logic.

## Relationship to Generated-AST Fixture Contract

- The generated-AST fixture contract may inform the internal value model.
- The generated-AST fixture contract is not the final runtime model.
- The generated-AST fixture contract exists to feed test vectors into scaffold serializers.
- The future internal value model may use different language-specific types.
- C and C++ may implement separate internal model representations.
- C++ must not reuse C runtime data structures as an implementation dependency unless explicitly documented as test fixture only.

## Relationship to Public API

- The internal value model is not a public API.
- The internal value model does not define a storage schema.
- The internal value model does not define a provider config schema.
- The internal value model does not expose generic JSON parsing to users.
- Any future public API must be separately designed and documented.

## Required Follow-up Before Implementation

The following are logical prerequisites that must be completed:
- add safe-integer boundary vectors (before implementation)
- add integer rejection vectors (before implementation)
- add UTF-16 object-key ordering vectors (before implementation)
- decide embedded NUL / `\u0000` support (before implementation)
- decide exact object duplicate-key rejection boundary (before implementation)
- decide internal construction/ownership rules for C (before implementation)
- decide internal construction/ownership rules for C++ (before implementation)
- decide whether model-level errors need standardized names (before public API exposure)
- then implement parser-free generic serializer in a later stride

## Explicit Non-Goals

This stride does not implement:
- generic JCS
- internal value model structs
- public value model API
- raw JSON parser
- third-party dependencies
- provider config validation
- metadata table validation
- floating-point canonicalization
- arbitrary precision number handling
- UTF-16 non-ASCII sort implementation
- cryptographic use
- SQLite support
- matrix integration
- production public APIs
