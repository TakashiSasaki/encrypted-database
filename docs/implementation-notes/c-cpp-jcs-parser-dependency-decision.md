# C/C++ JCS Parser and Dependency Decision

## Status
Accepted

## Context
Storage Format V1 requires strict JSON Canonicalization Scheme (RFC 8785) for ALL JSON stored in the database, including any JSON bytes that are authenticated, hashed, indexed, or compared. Python and Node.js currently serve as the baseline implementations.

In contrast, the C and C++ implementations are independent, native bootstrap scaffolds. They currently provide only a limited internal generated-AST JCS basic-vector serializer scaffold.

Currently, C and C++:
- Do not have a generic JCS implementation.
- Do not have an arbitrary JSON parser.
- Do not expose public JCS APIs.

Furthermore:
- C and C++ are independent native scaffold implementations.
- C++ must not wrap or call a C JCS runtime implementation.
- The package manager scope is heavily constrained: Conan and vcpkg are strictly forbidden, and no unreviewed third-party dependencies may be added.

## Decision Questions
Before embarking on a generic JCS implementation for C and C++, several fundamental design questions must be resolved:
- Should future generic JCS accept raw JSON text or already parsed values?
- If raw JSON text is accepted, what parser should be used?
- If parsed values are accepted, who owns parsing and validation?
- Should C and C++ use third-party parser/canonicalization libraries?
- Should C and C++ implement parser-free generic serialization over an internal value model first?
- How should unsupported numbers, duplicate keys, invalid JSON text, and parse errors be represented?
- How should independent C and C++ implementations avoid divergence when canonicalizing JSON?

## Options Considered

### Option 1: Raw JSON input with a dependency-free parser implemented independently in C and C++
**Pros:**
- No external dependency required.
- Full control over parse errors and the strict RFC 8785 boundary.
- Provides a strong, self-contained portability signal.

**Cons:**
- High implementation complexity.
- Significant JSON parsing security and robustness burden.
- Duplicate implementation effort across C and C++.
- High risk of subtle behavioral divergence between C and C++.
- Must manually handle edge cases: duplicate keys, exact numeric precision, invalid UTF-8, and define a comprehensive parser error taxonomy.

### Option 2: Raw JSON input using third-party JSON parsers or JCS libraries
**Pros:**
- Lower implementation burden.
- Can leverage potentially mature parser behavior and security.

**Cons:**
- Requires extensive dependency review (license, security posture, maintenance, portability).
- The "no Conan/vcpkg" policy complicates cross-platform dependency adoption.
- If different libraries are chosen for C and C++, their behavior may diverge subtly.
- A third-party parser may not expose the exact duplicate-key or strict numeric behavior needed for the stringent JCS policy.

### Option 3: Parser-free generic serializer over an internal value model first
In this approach, future generic JCS would accept an internal, typed value model, not raw JSON text. Parsing remains explicitly out of scope initially. The current generated-AST fixture contract can inform the value model but must not be treated as the final public API. The boundary for this model is documented in the [C/C++ JCS Internal Value Model Decision](./c-cpp-jcs-internal-value-model-decision.md).

**Pros:**
- Lowest risk next step.
- Builds incrementally on the existing generated-AST conformance scaffold.
- Avoids premature parser security and dependency decisions.
- Allows C and C++ to remain independent implementations while using shared test vectors to enforce consistency.

**Cons:**
- Does not solve raw JSON text canonicalization.
- Still requires explicit policies for number canonicalization and UTF-16 object-key sorting.
- Public API design and the parser boundary remain deferred as future work.

### Option 4: Continue with generated-AST test scaffold only
**Pros:**
- No implementation risk.
- Preserves the current, stable state.

**Cons:**
- Provides no path toward a generic JCS implementation.
- Cannot support provider config or metadata table JCS validation in C/C++.
- Does not advance the C/C++ native conformance roadmap.

## Recommended Direction
We recommend **Option 3: Parser-free generic serializer over an internal value model first**. This option now has an accepted internal value model boundary document.

**Rationale:**
- It is the lowest-risk next implementation boundary.
- It builds logically on the existing generated-AST conformance scaffold without prematurely calcifying that scaffold into a public API. (Note: `future-boundary-plan.json` is not an active conformance suite for the current scaffold.)
- It defers and avoids the complex raw parser and dependency selection.
- It keeps the C and C++ implementations fully independent.
- It permits the use of shared test vectors to enforce strict cross-language canonicalization behavior.
- It cleanly isolates generic serialization logic from raw JSON parsing.

**Caveats:**
- This approach does not implement raw JSON canonicalization.
- This approach does not solve the eventual public API exposure.
- This approach does not solve provider config or metadata table validation.
- This approach does not yet settle all number canonicalization and UTF-16 sorting edge cases.

## Internal Value Model Boundary
While not implemented in this stride, a future generic serializer would operate over an internal value model boundary supporting:
- `null`
- boolean
- string
- integer (within a strictly defined safe range)
- array
- object (with string keys)

See the [C/C++ JCS Internal Value Model Decision](./c-cpp-jcs-internal-value-model-decision.md) for detailed boundaries.
- explicit representations for unsupported/future number cases (Note: Unsafe integer rejection is future generic-model behavior, not current generated-AST harness behavior. Embedded NUL support remains unsupported / needs-decision until length-aware string ownership and serialization rules are specified.)

**Constraints on the internal value model:**
- This value model is not a public API.
- This value model is not the SQLite storage format.
- This value model is not the provider config schema.
- It is strictly an internal implementation boundary designed solely for generic serializer conformance.
- It may be informed by the existing generated-AST fixture contract, but it should be allowed to evolve independently.

## Dependency Policy
For this stride and the accepted immediate future work:
- No third-party dependency is added.
- No vendored dependency is added.
- No Conan or vcpkg integration is added.

Any future dependency consideration must be separately reviewed for:
- License compatibility
- Security posture
- Maintenance activity
- Portability
- Deterministic behavior
- Strict duplicate-key behavior
- Precise numeric parsing behavior
- UTF-8 and Unicode handling
- Build integration (without using disallowed package managers)

## Required Follow-up Before Implementation
Before proceeding to implement the parser-free generic serializer, the following prerequisite work must be completed:
- Define the internal value model precisely.
- Decide the integer safe range.
- Decide how to explicitly represent unsupported numbers.
- Add explicit UTF-16 key ordering vectors.
- Add number-policy/rejection vectors.
- Decide the duplicate-key behavior intended for the eventual raw JSON parser phase.
- Decide the parser error taxonomy.
- Decide whether the generic serializer remains internal-only or will eventually become public.
- Update the C/C++ native conformance roadmap after these decisions are finalized.

## Explicit Non-Goals
This stride is strictly a documentation and decision phase. It explicitly does **not** implement:
- Generic JCS.
- An arbitrary JSON parser.
- A public JCS API.
- Provider config validation.
- Metadata table validation.
- Raw JSON parsing.
- Number canonicalization beyond the existing generated-AST scaffold.
- UTF-16 non-ASCII sort implementation.
- Cryptographic use cases (Argon2id, AES-GCM, key-wrap, payload encryption).
- SQLite support (read-only or writer).
- Integration into the read-only or write matrices.
- Production public APIs.
