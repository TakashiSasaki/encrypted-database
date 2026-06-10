# C/C++ Architecture Decision

## Status
`needs-decision`

## Context
The repository currently contains initial bootstrap scaffolds for both C (`c/`) and C++ (`cpp/`). These scaffolds are currently used for native conformance testing (such as AAD construction, JSON escaping, UUID validation, and content-type boundary validation) and are not yet production storage libraries.

Before introducing deeper dependencies like generic JCS, Argon2id, AES-GCM, and SQLite support, the project must determine the architectural relationship between the C and C++ implementations. Should C++ act as a wrapper around a shared C core, or should they evolve as completely independent implementations?

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
The decision remains `needs-decision`.

## Near-Term Guidance
- Continue developing independent C and C++ scaffold helpers for small validation boundaries.
- Do not introduce cross-language coupling yet.
- Revisit this decision before implementing JCS, Argon2id, AEAD, or SQLite support.
- Deep native work should not proceed too far without resolving this architecture decision.

## Consequences
- The scaffolds remain isolated and uncoupled.
- Development of core Storage Format V1 capabilities (JCS, crypto, DB access) is blocked pending this decision.
- Future refactoring may be required if work proceeds independently but the project later decides on a unified C core.

## Revisit Triggers
- When planning the generic JCS implementation.
- When planning Argon2id or AES-256-GCM dependency integration.
- When planning SQLite V1 integration.
