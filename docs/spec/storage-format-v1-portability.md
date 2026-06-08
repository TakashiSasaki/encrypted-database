# Storage Format V1 Portability Validation Policy

## 1. Purpose
This document defines the approach and policy for validating the portability of Storage Format V1 as the Encrypted Database project expands its scope to native compiled languages, specifically Go, Rust, and Zig. It outlines how portability issues discovered during this phase are tracked, classified, and resolved.

## 2. Stable Baseline Definition
Storage Format V1 has been formally declared **Stable**. This stability designation is defined as a tested and verified baseline operating seamlessly across the Python, Node.js, and browser-test environments. The core format schema, metadata table constraints (including strict UUID policy enforcement), strict JCS requirements, and cryptographic compatibility within these domains are considered a mature baseline.

The `tag-1.z.z` tag marks the Storage Format V1 stable baseline used for Go/Rust/Zig portability validation. Any findings are evaluated as deviations from this `tag-1.z.z` baseline.

## 3. Portability Validation Scope
The Go, Rust, and Zig portability validation efforts focus on building a portability validation harness, consuming existing test vectors (JCS, AAD, KDF, AEAD, etc.), and developing read-only readers and writer scaffolds. The goal is to surface any hidden ambiguities, type assumptions, or standard library limitations that exist in stricter compiled ecosystems.

## 4. Issue Classification
Issues discovered during portability validation will be recorded in the `docs/implementation-notes/portability-findings.md` log and classified using one of the following tags:

- **clarification**: No changes to the storage format or validation rules are necessary. Requires only clearer wording in the specification documentation.
- **implementation-note**: An implementation-specific detail (e.g., specific to a language, driver, or library) that does not alter the specification but provides necessary context for future implementers.
- **future-v2-item**: A breaking change that would invalidate existing V1 databases and should be deferred to a hypothetical V2 design.
- **implementation-bug**: A bug in an existing implementation (Python, Node.js, or browser-test) that does not comply with the written specification.
- **test-gap**: The specification and implementation are correct, but the testing suite (e.g., test vectors) lacks sufficient coverage.
- **test-vector-correction**: The specification is correct, but a test vector or fixture is incorrect and needs to be updated to match the existing V1 specification.
- **driver-or-library-limitation**: An issue arising from limitations in third-party components like SQLite drivers, Argon2id, JCS, or AES-GCM libraries. This should be documented as an implementation note or limitation, not treated as a format amendment.

*(Historical Note: Early in the portability validation process, before public adoption, a **controlled-v1-amendment** category was temporarily used. This is no longer an active classification path now that V1 is treated as strictly Stable).*

## 5. Stability and Evolution Policy
The fundamental principle of the Stable designation is that Storage Format V1 should remain unchanged.

Incompatible changes to bytes-on-disk semantics, metadata semantics, JCS rules, AAD rules, AEAD envelope layout, UUID policy, feature/version policy, or SQLite Storage Profile semantics MUST NOT be made casually and must be deferred to a future Storage Format V2.

However, evolution within V1 is permitted under strict conditions:
- **Non-breaking clarifications** are allowed when they clarify current V1 behavior without changing semantics.
- **Implementation bug fixes** are allowed when they bring code into conformance with the existing V1 specification.
- **Test vector corrections** are allowed when they correct tests or fixtures to match the existing V1 specification.

## 6. Non-Breaking Clarifications
Clarifications to the written specification that do not alter physical bytes on disk, constraint rules, or cryptographic algorithms will be accepted freely. This ensures documentation accuracy is maintained without destabilizing V1.

## 7. Future V2 Deferral Criteria
Any issue that requires breaking backwards compatibility with databases created by the current stable Python, Node.js, or browser-test implementations will be strictly deferred to a future V2 format.

## 8. Go/Rust/Zig Validation Milestones
The Go, Rust, and Zig portability validation efforts have advanced beyond initial test vector discovery. The current milestones are tracked as follows:

Go/Rust have more mature portability validation and writer scaffolds.
Zig currently has an initial partial read-only validation scaffold with shared-vector conformance.

**Already materially implemented / validated (Go/Rust):**
- shared test-vector consumption
- JCS / AAD / KDF / AEAD / key-wrap / payload vector validation
- SQLite V1 metadata validation
- read-only unlock/decrypt readers
- writer scaffolds for create / insert / update / delete
- read-only matrix harness
- write-matrix harness
- path-filtered CI for relevant matrix workflows

**Already materially implemented / validated (Zig):**
- Shared test-vector conformance (JCS, AAD, KDF, AEAD, key-wrap, payload)
- SQLite V1 metadata validation

**Still incomplete / future work:**
- full production Go/Rust storage libraries
- stable public API parity
- full key lifecycle operations
- rewrap
- additional unlock providers
- blind index
- Python/Node.js writer outputs in write-matrix
- browser export/import matrix coverage
- Go/Wasm full SQLite-backed support
- Zig read-only unlock/decrypt reader
- Zig writer scaffold
- Zig read-only matrix integration
- Zig write-matrix integration

Note: Go, Rust, and Zig implementations remain strictly portability validation and writer scaffolds, not full production storage libraries.

## 9. Relationship to Stable Declaration
The Go/Rust/Zig validation efforts do not revoke the Storage Format V1 Stable declaration. The stable format serves as the canonical target for these new implementations to aim for.

## 10. Reporting and Decision Process
All issues must be entered into the Portability Findings Log. Complex issues should be reviewed and decided upon before any corresponding implementation changes are initiated.
