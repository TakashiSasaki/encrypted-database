# C/C++ Architecture Decision

## Status
`decided`

## Context
The repository currently contains initial bootstrap scaffolds for both C (`c/`) and C++ (`cpp/`). These scaffolds are currently used for native conformance testing (such as AAD construction, JSON escaping, UUID validation, content-type boundary validation, and a limited generated-AST JCS basic-vector serializer scaffold) and are not yet production storage libraries.

Before introducing deeper dependencies like generic JCS, Argon2id, AES-GCM, and SQLite support, the project needed to determine the architectural relationship between the C and C++ implementations. The decision was whether C++ should act as a wrapper around a shared C core, or if they should evolve as completely independent implementations.

## Options Considered

### Option 1: C core with C++ wrapper
In this model, the core cryptographic, JCS, and SQLite logic is implemented in C. The C++ implementation primarily acts as a higher-level, safer, idiomatic API wrapper utilizing RAII and C++ standard library types over the C ABI.

**Pros:**
- Single native implementation core, reducing bugs and maintenance burden.
- Less duplicated logic for complex areas like JCS, cryptography, and SQLite integration.
- Provides an easier ABI boundary for foreign language integrations that expect a C ABI.
- C++ can provide safer RAII wrappers later on top of a proven core.

**Cons:**
- C++ design becomes constrained by the underlying C ABI and memory ownership model.
- Harder to use idiomatic C++ internally for processing data.
- The C error model and memory ownership must be designed strictly and early.

### Option 2: Independent C and C++ implementations
In this model, the C and C++ implementations are entirely separate. C++ implements its own JCS, cryptography, and SQLite integrations natively using idiomatic C++ abstractions.

**Pros:**
- C++ can be fully idiomatic and utilize RAII, standard strings, and vectors from the ground up without ABI constraints.
- Independent implementations can catch portability assumptions or specification ambiguities.
- Simpler early scaffold evolution without worrying about cross-language linkage.

**Cons:**
- High amount of duplicated logic, increasing the overall maintenance burden.
- Higher risk of divergence between the two implementations.
- Cryptographic and SQLite behavior must be carefully kept in sync manually.

### Option 3: Hybrid model
A shared C library for low-level primitives (like specific cryptographic wrappers or JCS primitives), but independent C++ orchestration and higher-level database operations.

## Current Decision
**Option 2: Independent C and C++ implementations** has been accepted.

C and C++ are intentionally independent native scaffold implementations. C++ is not planned as a wrapper around a common C core. Both implementations may use language-idiomatic internals: C may use explicit ownership, C structs, CMake, and C-style APIs internally, while C++ may use RAII, `std::string`, `std::vector`, `std::string_view`, and other idiomatic C++ abstractions.

This independence does not mean behavioral divergence is allowed. Both implementations must conform to the same Storage Format V1 specification, shared test vectors, CI expectations, and documentation vocabulary. Any future divergence must be explicitly documented as a language-boundary difference, not accidental drift. This decision does not mean either implementation is production-ready, nor does it immediately start generic JCS, cryptography, or SQLite implementation work.

## Consequences
- Duplicate implementation effort is accepted.
- Independent implementations increase portability-validation value and language-native clarity over a single native core.
- Shared vectors and cross-language tests become mandatory guardrails.
- Documentation must distinguish implementation independence from conformance divergence.
- C and C++ must continue to be tested separately.
- Future differences must be explicitly documented as language-boundary decisions, not accidental drift.

## Revisit Triggers
- When planning the generic JCS implementation.
- When planning Argon2id or AES-256-GCM dependency integration.
- When planning SQLite V1 integration.
