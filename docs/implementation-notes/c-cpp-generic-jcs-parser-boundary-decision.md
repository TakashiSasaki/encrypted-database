# C/C++ Generic JCS Parser Boundary Decision

## Status
Accepted

## Context
The C and C++ generic JCS implementations currently rely on a generated-AST fixture contract (`rfc8785-basic.json`) as a basic conformance smoke test. The project has accepted the strategy of building a **parser-free generic serializer** over an internal value model before attempting raw JSON parsing.

This document clearly defines the boundary and layers between the parser-free internal model serialization, generated-AST fixture serialization, future generic JSON vector loading, future raw JSON parsing, and future rejection-vector harnesses. The goal is to explicitly reduce ambiguity before generic JCS parser or generic vector harness implementations begin.

## Parser Boundary Decision
**Decision:** The next implementation boundary remains parser-free internal value model serialization. Raw JSON parsing remains explicitly deferred.

### Rationale
- Raw JSON parsing introduces complex requirements including duplicate-key handling policies, number precision fidelity, invalid UTF-8 detection, string escape decoding, and the definition of a comprehensive parse error taxonomy.
- Parser-free model serialization has already matured significantly in the form of C/C++ internal models, robust UTF-16 comparator hardening, and internal API direct tests.
- `utf16-key-ordering.json` serves strictly as a non-active positive seed and is verified via a standalone helper, not through active generated bridges.
- `future-boundary-plan.json` is strictly planning-only and must not be consumed as an active harness source.

### Boundary Definitions
- **What remains parser-free?** The core generic serializer. It strictly operates on the in-memory internal value model, completely bypassing text parsing.
- **What requires a raw parser?** Processing raw JSON text blocks directly into internal values, decoding Unicode escapes, enforcing numeric format constraints natively, and deciding how to reject invalid JSON syntax natively.
- **What is a generic vector loader?** A future test-harness mechanism that will read generic positive JSON vectors (e.g. ones with `"input"`, `"expected_string"`, and `"expected_hex"`) and programmatically build the C/C++ parser-free internal models necessary to test canonicalization. This is distinct from a raw JSON parser API meant for end users.
- **What is a rejection harness?** A future test-harness layer dedicated to running test vectors designed to fail (e.g., negative tests, unsafe integers, duplicate keys). This is completely separate from positive vector canonicalization.
- **What is still generated-AST-only?** The current runtime bridge. The generated-AST fixture bridges remain limited to parsing `rfc8785-basic.json` via struct instantiations unless a future decision explicitly expands them.
- **What is future production API work?** Exposing the JCS canoncalization functionality to broader systems via public C/C++ interfaces, integration into cryptography providers, metadata table structures, or public API exposure.

## Layered Architecture
To manage implementation risk, we document the following layered architecture:

1. **Generated-AST fixture bridge**
   - **Input:** Generated C/C++ structs from `rfc8785-basic.json`.
   - **Current status:** Active scaffold.
   - **Purpose:** Basic conformance smoke coverage.
   - **Not generic JCS.**

2. **Parser-free internal model serializer**
   - **Input:** Explicitly constructed C/C++ internal model values.
   - **Current status:** Implemented for null, boolean, safe integer, string, array, object, UTF-16 ordering.
   - **Purpose:** Generic serializer core without raw parser risk.
   - **Not raw JSON canonicalization.**

3. **Standalone non-active positive vector verification**
   - **Input:** JSON vector files such as `utf16-key-ordering.json`.
   - **Current status:** Standalone Python verifier for UTF-16 seed.
   - **Purpose:** Baseline expected-output verification.
   - **Not C/C++ harness integration.**

4. **Future generic JSON vector loader**
   - **Input:** Positive vector files with `"input"`, `"expected_string"`, `"expected_hex"`.
   - **Purpose:** Load generic JSON values from vector files and construct internal model values for C/C++ tests.
   - **Details:** Requires explicit handling of safe integers, strings, arrays, objects, duplicate-key constraints as applicable.
   - **Not a public parser API.**

5. **Future raw JSON parser**
   - **Input:** Raw JSON text.
   - **Purpose:** Parse arbitrary JSON text into internal values.
   - **Details:** Must handle duplicate keys, escape decoding, invalid UTF-8, exact number policy, and produce a unified parse error taxonomy.
   - **Future only.**

6. **Future rejection-vector harness**
   - **Input:** Future rejection vectors such as unsafe integers, duplicate keys, embedded NUL, invalid JSON.
   - **Purpose:** Assert fail-closed behavior on boundaries.
   - **Future only.**

## Vector Suite Policy
The status of each JSON test vector source is defined as follows:

- `test-vectors/jcs/rfc8785-basic.json`
  - Active generated-AST positive vectors.
  - Must remain strict-loader-compatible.
  - No ad hoc metadata fields are allowed.

- `test-vectors/jcs/utf16-key-ordering.json`
  - Non-active positive seed.
  - Baseline verified via standalone Python helper.
  - Not wired into C/C++ generated bridge tests.
  - Candidate for future generic vector loader or a dedicated UTF-16 harness decision.

- `test-vectors/jcs/future-boundary-plan.json`
  - Planning-only documentation.
  - Not an active conformance source.
  - Must not be consumed by any C/C++ test runners.
  - Can inform future vector taxonomy and rejection harness design decisions.

## Proposed Implementation Sequence
The following is the proposed safe sequence of steps to advance the C/C++ JCS implementation:

1. Generic JCS parser boundary decision and generic vector harness architecture plan. *(This document)*
2. C/C++ parser-free internal model conformance review.
3. Generic positive vector loader design.
4. Generic positive vector loader scaffold for parser-free model construction.
5. UTF-16 positive vector loader integration.
6. Safe integer / number-policy positive and rejection vector design.
7. Rejection-vector harness decision.
8. Raw JSON parser dependency/security decision.
9. Raw JSON parser scaffold, if still desired.
10. Public API decision, if still desired.

*(Note: None of these steps beyond step 1 are implemented in the current stride.)*
