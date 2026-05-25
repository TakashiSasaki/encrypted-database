# Storage Format V1 Portability Validation Policy

## 1. Purpose
This document defines the approach and policy for validating the portability of Storage Format V1 as the Encrypted Database project expands its scope to native compiled languages, specifically Go and Rust. It outlines how portability issues discovered during this phase are tracked, classified, and resolved.

## 2. Stable Baseline Definition
Storage Format V1 has been formally declared **Stable**. This stability designation is defined as a tested and verified baseline operating seamlessly across the Python, Node.js, and browser-test environments. The core format schema, metadata table constraints, strict JCS requirements, and cryptographic compatibility within these domains are considered a mature baseline.

The `tag-1.z.z` tag marks the Storage Format V1 stable baseline used for Go/Rust portability validation. Any findings, including controlled V1 amendments, are evaluated as deviations from this `tag-1.z.z` baseline.

## 3. Portability Validation Scope
The initial Go and Rust efforts focus on building a portability validation harness and consuming existing test vectors (JCS, AAD, KDF, AEAD, etc.) rather than immediately delivering full-featured read/write database libraries. The goal is to surface any hidden ambiguities, type assumptions, or standard library limitations that exist in stricter compiled ecosystems.

## 4. Issue Classification
Issues discovered during portability validation will be recorded in the `docs/implementation-notes/portability-findings.md` log and classified using one of the following tags:

- **clarification**: No changes to the storage format or validation rules are necessary. Requires only clearer wording in the specification documentation.
- **implementation-note**: An implementation-specific detail (e.g., specific to a language, driver, or library) that does not alter the specification but provides necessary context for future implementers.
- **controlled-v1-amendment**: A change to the storage format or validation rules is required to ensure portability. See the Controlled V1 Amendment Policy below.
- **future-v2-item**: A breaking change that would invalidate existing V1 databases and should be deferred to a hypothetical V2 design.
- **implementation-bug**: A bug in an existing implementation (Python, Node.js, or browser-test) that does not comply with the written specification.
- **test-gap**: The specification and implementation are correct, but the testing suite (e.g., test vectors) lacks sufficient coverage.
- **driver-or-library-limitation**: An issue arising from limitations in third-party components like SQLite drivers, Argon2id, JCS, or AES-GCM libraries.

## 5. Controlled V1 Amendment Policy
The fundamental principle of the Stable designation is that Storage Format V1 should remain unchanged. However, because the library currently has no external production users, there is a limited window to implement controlled V1 amendments if critical ambiguities or unresolvable portability blockers are found during the Go/Rust validation phase.

If a **controlled-v1-amendment** is deemed necessary:
1. The issue MUST be thoroughly documented in the findings log.
2. The impact on the existing stable baseline (Python/Node.js/browser-test), test vectors, and documentation MUST be explicitly defined as differences from the `tag-1.z.z` baseline.
3. The amendment MUST be carried out as an isolated task, not bundled directly with portability implementation scaffolding.

## 6. Non-Breaking Clarifications
Clarifications to the written specification that do not alter physical bytes on disk, constraint rules, or cryptographic algorithms will be accepted freely. This ensures documentation accuracy is maintained without destabilizing V1.

## 7. Future V2 Deferral Criteria
Any issue that requires breaking backwards compatibility with databases created by the current stable Python, Node.js, or browser-test implementations will be strictly deferred to a future V2 format, unless they meet the criteria for a controlled V1 amendment prior to public adoption.

## 8. Go/Rust Validation Milestones
The current phase focuses solely on test vector discovery and execution (the scaffold/harness). Subsequent phases will build cryptographic primitives and eventually full database interaction (roundtrips).

## 9. Relationship to Stable Declaration
The Go/Rust validation efforts do not revoke the Storage Format V1 Stable declaration. The stable format serves as the canonical target for these new implementations to aim for.

## 10. Reporting and Decision Process
All issues must be entered into the Portability Findings Log. Complex issues should be reviewed and decided upon before any corresponding implementation changes are initiated.
