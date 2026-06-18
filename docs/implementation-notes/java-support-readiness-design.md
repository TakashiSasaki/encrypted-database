# Java Support Readiness Design and JVM Scaffold Boundary

## Scope
- Java is a future JVM target.
- Initial goal: Parity planning and scaffold boundary.
- Non-goal: No production Java storage library in this stride.
- Non-goal: No Maven Central or package publication.

## Required Storage Format V1 Invariants
- bytes-on-disk compatibility;
- JCS canonical exactness;
- Argon2id profile compatibility;
- AES-GCM / AEAD envelope compatibility;
- AAD exactness;
- SQLite Storage Profile compatibility;
- UUID canonical validation;
- metadata validation;
- feature/version policy.

## Java-Specific Risk Inventory
- JCS/RFC 8785 canonicalization and numeric formatting risks;
- duplicate JSON key detection;
- Unicode ordering and escaping;
- AES-GCM tag length and AAD behavior through JCA or provider APIs;
- Argon2id library selection and parameter exactness;
- SQLite/JDBC dependency and native binding policy;
- byte array / UTF-8 handling;
- UUID parsing strictness versus Java built-in UUID permissiveness;
- filesystem and temporary file handling;
- deterministic test fixtures;
- package namespace and module naming, still undecided.

## Candidate Dependency Decision Points
- JSON/JCS library decision: needs-decision
- Argon2id provider decision: needs-decision
- SQLite/JDBC provider decision: needs-decision
- cryptographic provider decision: needs-decision
- test framework decision: needs-decision
- build tool decision: needs-decision

## Proposed Java Readiness Phases
- Phase J0: design and risk inventory. (Current Phase)
- Phase J1: read-only metadata/parser scaffold.
- Phase J2: test-vector consumer for shared fixtures.
- Phase J3: read-only decrypt compatibility.
- Phase J4: write-path scaffold.
- Phase J5: cross-language matrix participation.
- Phase J6: public API candidate.
- Phase J7: baseline-public certification candidate.

*Note: Only J0 is in scope for this stride.*

## Cross-Language Validation Plan
- Java must first consume existing shared vectors.
- Java must not introduce new Storage Format V1 semantics.
- Java write support must not be considered until Java read compatibility is proven.
- Java's future baseline-public status requires direct public API matrix and installed-distribution-like validation in a future phase.

## Readiness Classification
- Current Java status: "needs-decision" or "out-of-scope".
- Do not use "implemented-public".
- Do not use "baseline-public".
