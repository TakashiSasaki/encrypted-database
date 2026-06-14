# C/C++ Native Conformance Roadmap

This document outlines the planned stages for expanding the C and C++ native conformance scaffolds. Currently, these implementations are strictly **bootstrap scaffolds** and are not production storage libraries.

They do not yet implement full Storage Format V1 cryptography, Argon2id, generic JSON Canonicalization Scheme (JCS), SQLite V1 read-only validation, writing capabilities, or integration into the read-only or write matrices.

The immediate goal is to incrementally establish a native testing boundary and validate cross-language test vectors before attempting integration.

## Roadmap Stages

### Completed
- **Cross-language read/write compatibility matrix baseline (discovery/execution implemented for baseline languages)**
- **C/C++ parser-free JCS serializer semantic hardening**
- **Generic positive vector loader runtime-vector wiring decision**
- **Generic positive vector build-time fixture wiring**
- **Bootstrap build/test scaffold**
- **Partial AAD shared-vector conformance**
- **Internal JSON escaping for AAD construction**
- **Internal UUID syntax validation scaffold**
- **Internal content-type boundary validation scaffold**
- **Documentation consistency cleanup**
- **JCS scaffold boundary decision**
- **Limited generated-AST JCS basic-vector serializer scaffold**
- **C/C++ independent implementation architecture decision**
- **JCS fixture contract cleanup**
- **JCS vector expansion and classification**
- **Generic JCS implementation strategy decision (Accepted)**
- **Generic JCS parser/dependency decision (Accepted)**
- **Generic JCS internal value model decision (Accepted)**
- **Generic JCS boundary-vector plan**
- **Initial generic JCS safe-integer positive boundary-vector seed**
- **Initial generic JCS future boundary-vector classification plan**
- **Generic JCS future boundary-vector representation decision**
- **Additional active positive JCS boundary-vector tranche**
- **Future JCS rejection-vector harness decision**
- **UTF-16 key-ordering vector planning**
- **C/C++ parser-free generic JCS runtime readiness package**
- **C parser-free JCS internal model scaffold**
- **C parser-free JCS internal model array/object scaffold**
- **C parser-free JCS internal model serializer seed**
- **C parser-free JCS model serializer hardening**
- **C parser-free JCS model serializer vector bridge**
- **C parser-free JCS model serializer vector bridge expansion**
- **C++ parser-free JCS internal model scaffold**
- **C++ parser-free JCS internal model serializer seed**
- **C++ parser-free JCS model serializer hardening**
- **C++ parser-free JCS generated-vector bridge**
- **C/C++ parser-free JCS bridge parity cleanup**
- **UTF-16 key-ordering implementation planning**
- **C/C++ UTF-16 key comparator prototype**
- **C/C++ UTF-16 comparator hardening**
- **UTF-16 key-ordering vector activation decision**
- **UTF-16 key-ordering positive vector seed**
- **Generic JCS parser boundary decision**
- **C/C++ parser-free internal model conformance review**
- **Generic positive vector loader design**
- **Generic positive vector loader scaffold**
- **Generic positive vector loader scaffold hardening**
- **Generic positive vector coverage expansion**
- **Generic JCS implementation boundary review**

### Near-term

#### Phase 1: Scaffold Maturation and Conformance-Boundary Planning
- **Generic positive JCS vector loader scaffold hardening**: Follow-through on the generic positive JCS vector loader design to harden the scaffold implementation, specifically targeting safety boundaries and testing integration rather than raw JSON parsing.
- **Active vs non-active JCS vector consumption strategy**: Formally document the strategy for consuming JCS test vectors. This includes ensuring active positive vectors are consumed by tests, while explicitly maintaining `future-boundary-plan.json` as planning-only (not consumed by test runners without a later explicit decision).
- **Explicit classification of JCS vectors**: Clearly document the classification of active positive vectors (including `utf16-key-ordering.json` for the positive-loader scaffold), non-active seed vectors, and planning-only vectors, strictly controlling which are wired into the C/C++ scaffolds.
- **C/C++ shared-vector conformance expansion**: Expand shared-vector conformance testing strictly where it remains a scaffold-level, test-vector-oriented validation.
- **Documentation consistency**: Ensure all READMEs, gap documents, and roadmap documents accurately reflect that C and C++ are independent bootstrap scaffolds, avoiding overclaims regarding generic JCS completeness or production readiness.

### Future
- **Generic JCS implementation**
- **Argon2id dependency decision**
- **Argon2id vector conformance**
- **AES-256-GCM dependency decision**
- **AEAD vector conformance**
- **Key-wrap vector conformance**
- **Payload encryption vector conformance**
- **SQLite read-only fixture validation**
- **Read-only decrypt scaffold**
- **Writer scaffold**
- **Matrix integration**
- **Production public API decision**

*Note: This roadmap is intended for planning purposes only and does not imply that cryptographic or SQLite implementation work has commenced.*
