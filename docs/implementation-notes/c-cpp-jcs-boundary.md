# C/C++ JCS Boundary

## Status
`scaffold-decision`

## Decision

For the current stride in the C and C++ bootstrap scaffolds, we are adding a **limited internal generated-AST JCS basic-vector serializer scaffold**.

We have decided:
- C/C++ will not add a third-party JCS dependency in this stride.
- C/C++ will not add a JSON parser in this stride.
- C/C++ will not expose public JCS APIs in this stride.
- C/C++ will add a limited internal shared-vector scaffold using generated AST fixtures from `test-vectors/jcs/rfc8785-basic.json`.

This scaffold validates canonical serialization behavior for the current basic shared vectors. It is not a full RFC 8785 implementation, and it does not imply production public API parity. It does not resolve the C/C++ architecture decision, and it must be revisited before Argon2id, AEAD, SQLite, or public API work.

## Coverage Boundary

**Supported in this scaffold:**
- object serialization
- lexicographic object key sorting
- arrays
- strings
- UTF-8 byte preservation
- required JSON string escaping
- integers representable in signed 64-bit range
- booleans and null

**Explicitly unsupported or out of scope:**
- arbitrary JSON parsing
- floating-point canonicalization
- arbitrary precision number handling
- Unicode normalization
- public API validation
- database metadata validation
- provider config validation
- cryptographic use
