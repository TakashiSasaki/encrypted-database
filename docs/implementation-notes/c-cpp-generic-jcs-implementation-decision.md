# C/C++ Generic JCS Implementation Decision

## Status
Proposed

## Context
The C and C++ implementations are independent, native conformance scaffolds. Currently, they feature a limited internal generated-AST JCS basic-vector serializer scaffold.

- C/C++ do not have a generic JSON parser.
- C/C++ do not have full RFC 8785 coverage.
- Python and Node.js are the baseline implementations.
- Storage Format V1 requires JCS-normalized JSON for any byte sequences stored, authenticated, hashed, or compared, where applicable.
- The implementations share test fixtures and conformance expectations, but runtime serializer and parser implementations remain fully independent. C++ does not wrap the C serializer.

## Decision Scope
This document proposes a strategy for the future implementation of generic JCS in C and C++. It specifically distinguishes between:
- Current scaffold behavior (limited generated-AST serialization)
- Future generic JCS implementation
- Future public API exposure
- Future metadata and provider config validation
- Future cryptographic uses

## Options Considered

### Option 1: Implement dependency-free generic JCS in each language.
**Pros:**
- No third-party dependencies required.
- Complete control over RFC 8785 behavior.
- Provides a strong, useful portability-validation signal.

**Cons:**
- High implementation risk.
- Tricky canonicalization requirements for numbers (e.g., float bounds, arbitrary precision).
- Tricky UTF-16 object key ordering edge cases.
- Risk of behavioral divergence between C and C++ implementations.

### Option 2: Use a third-party JSON/JCS library per language.
**Pros:**
- Lowers implementation burden significantly.
- May provide mature parsing and canonicalization behavior out of the box.

**Cons:**
- Requires careful dependency review.
- Conflicts with the current C/C++ package-manager policy, which forbids Conan and vcpkg.
- Different libraries chosen for C and C++ may subtly diverge in behavior.
- Introduces license, security, and cross-platform compilation concerns.

### Option 3: Hybrid staged approach.
Use the current generated-AST serializer scaffold as the first stage. Add official and repository-specific JCS vectors to flesh out edge cases. Decide on the parser/dependency separately later. Introduce generic JCS only after policies for number handling and UTF-16 sorting are rigorously documented.

## Recommended Direction
We recommend **Option 3: Hybrid staged approach** as the proposed path.

Specifically, the implementation plan is to:
1. Keep the current generated-AST scaffold as the conformance seed.
2. Expand and classify JCS test vectors before attempting full implementation.
3. Do not add a JSON parser yet.
4. Do not add third-party dependencies yet.
5. Document the parser/dependency decision in a separate, later stride.
6. Document number handling and UTF-16 object-key sorting explicitly before implementation.
7. Only then, proceed to generic JCS implementation.

This is a proposed strategy, not a completed implementation.

## Required Coverage Before Implementation
Before generic JCS is implemented, the following RFC 8785 boundaries and edge cases must be explicitly resolved and documented:

### UTF-16 Object Member Sorting
- Handling of non-ASCII keys.
- Surrogate-pair-sensitive ordering.

### Number Canonicalization
- Floats and decimals.
- Exponent notation handling.
- Negative zero (`-0`).
- Large integers outside the exact IEEE-754 safe integer range.
- Arbitrary precision numbers.

### Unicode Handling
- Strict UTF-8 byte preservation.
- Ensuring no unintended Unicode normalization occurs during parsing.
- Correct escaping of control characters.

### Invalid Input Behavior
- Rejection policy for unsupported numbers.
- Behavior regarding duplicate object keys (if parser behavior exposes them).
- Ensuring non-string object keys are treated as invalid JSON and never canonicalized.

### Parser Boundary
- Defining whether the future C/C++ generic JCS layer accepts parsed in-memory values only, or raw JSON text.
- If raw JSON text is accepted, explicitly deciding what parser is used and how parse errors are surfaced.

## Explicit Non-Goals
This decision document does **not** implement:
- Generic JCS.
- An arbitrary JSON parser.
- A public JCS API.
- Provider config validation.
- Metadata table validation.
- Cryptographic use.
- SQLite support.
- Matrix integration.
- Production public APIs.

## Revisit Triggers
This proposed strategy must be revisited:
- Before adding any generic JCS source code.
- Before choosing or adding any third-party dependency.
- Before adding JSON parser support.
- Before using C/C++ JCS output in cryptographic test vectors.
- Before exposing any public API.
