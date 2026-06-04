# Encrypted Database Documentation

This directory contains the documentation, specifications, and architectural decisions for the Encrypted Database project.

## Table of Contents

- [How to Read the Docs](#how-to-read-the-docs)
- [Canonical Sources](#canonical-sources)
- [Existing Documents](#existing-documents)
  - [Specifications](#specifications)
  - [Backend & Storage](#backend--storage)
  - [Providers](#providers)
  - [Architecture Decision Records (ADRs)](#architecture-decision-records-adrs)
  - [Implementation Notes](#implementation-notes)
  - [Legacy](#legacy)

## How to Read the Docs

For future contributors, please read the documentation in the following order:
1. Start with this **README** to understand the documentation structure.
2. Read the **Overview and Terminology** (`docs/spec/overview.md`, `docs/spec/terminology.md`) to grasp the system's core concepts.
3. Review the **Architecture Decision Records (ADRs)** in `docs/decisions/` to understand the resolved design decisions and foundational rules.
4. Review the **SQLite Schema and Constraints** (`docs/backend/sqlite/schema.md`, `docs/backend/sqlite/constraints.md`) to understand the canonical database storage layer.
5. Check `docs/spec/open-questions.md` and `docs/implementation-notes/implementation-gaps.md` for ongoing design work and areas where implementations are still catching up to the spec.

## Canonical Sources

The documentation has been refactored into focused modules.

- **Schema Truth**: `docs/backend/sqlite/schema.sql` is the concrete, canonical SQLite schema source.
- **Specification Truth**: The documents in `docs/spec/` represent the current, authoritative design and operations model.
- **Decision Truth**: The ADRs in `docs/decisions/` represent fundamental design choices.

## Existing Documents

*Note: Go and Rust directories are currently portability-validation scaffolds (now including SQLite V1 read-only metadata validators). They are intended to consume shared conformance vectors, validate read/write scaffold interoperability, and uncover portability issues before full production storage libraries are developed. Storage Format V1 is Stable. Go/Rust portability work validates the stable format. Remaining issues should be tracked as implementation gaps, non-breaking clarifications, implementation bugs, test gaps, test vector corrections, driver/library limitations, or future V2 items. The library as a whole is not yet declared production-ready.*

### Specifications
- [`spec/overview.md`](./spec/overview.md): High-level system overview and principles.
- [`spec/terminology.md`](./spec/terminology.md): Definitions, identifier rules (UUIDv4), and JSON Canonicalization rules.
- [`spec/key-hierarchy.md`](./spec/key-hierarchy.md): Detailed layout of the encryption key hierarchy.
- [`spec/envelope-format.md`](./spec/envelope-format.md): Formatting rules for versioned AEAD envelopes.
- [`spec/aad-policy.md`](./spec/aad-policy.md): Rules for generating and binding Additional Authenticated Data.
- [`spec/provider-platform-model.md`](./spec/provider-platform-model.md): Abstract vs concrete unlock models and platform binding rules.
- [`spec/api-contract.md`](./spec/api-contract.md): Cross-language API operations, lifecycle state definitions, and error taxonomies.
- [`spec/lifecycle.md`](./spec/lifecycle.md): State diagram illustrating the database lifecycle.
- [`spec/operations.md`](./spec/operations.md): Standard operational flows (e.g., creating DBs, storing payloads).
- [`spec/blind-index.md`](./spec/blind-index.md): Searchability via HMAC blind indexing.
- [`spec/security-model.md`](./spec/security-model.md): Threat model, in-scope protections, and material handling policies.
- [`spec/test-vectors.md`](./spec/test-vectors.md): Requirements for cross-language compatibility testing.
- [`spec/storage-format-v1-readiness.md`](./spec/storage-format-v1-readiness.md): Storage Format V1 Stable Declaration Review.
- [`spec/storage-format-v1-portability.md`](./spec/storage-format-v1-portability.md): Go/Rust Portability Validation Policy and V1/V2 issue classification.
- [`spec/open-questions.md`](./spec/open-questions.md): Extracted unresolved design questions and ongoing considerations.

### Backend & Storage
- [`backend/sqlite/schema.sql`](./backend/sqlite/schema.sql): The canonical, concrete SQLite schema.
- [`backend/sqlite/schema.md`](./backend/sqlite/schema.md): Conceptual overview of the SQLite schema.
- [`backend/sqlite/er-diagram.md`](./backend/sqlite/er-diagram.md): Graphical ER diagram of the SQLite schema.
- [`backend/sqlite/constraints.md`](./backend/sqlite/constraints.md): Details on foreign keys, PRAGMAs, and strict version constraints.

### Providers
- [`providers/passphrase-argon2id.md`](./providers/passphrase-argon2id.md): Standard Argon2id default parameters and provider details.

### Architecture Decision Records (ADRs)
- [`decisions/README.md`](./decisions/README.md): Index of Architecture Decision Records.
- [`decisions/ADR-0001-use-uuid-canonical-kid.md`](./decisions/ADR-0001-use-uuid-canonical-kid.md): Stable key identifiers.
- [`decisions/ADR-0002-require-rfc8785-jcs.md`](./decisions/ADR-0002-require-rfc8785-jcs.md): JSON canonicalization.
- [`decisions/ADR-0003-prohibit-cross-platform-platform.md`](./decisions/ADR-0003-prohibit-cross-platform-platform.md): Concrete platform names.
- [`decisions/ADR-0004-version-envelopes-from-v1.md`](./decisions/ADR-0004-version-envelopes-from-v1.md): Versioned envelopes from the first schema.
- [`decisions/ADR-0005-require-wrap-id.md`](./decisions/ADR-0005-require-wrap-id.md): Dedicated wrap ID in the schema.

### Implementation Notes
- [`implementation-notes/implementation-gaps.md`](./implementation-notes/implementation-gaps.md): Known gaps between the canonical specifications and the current implementations, including implementation issue history.
- [`implementation-notes/portability-findings.md`](./implementation-notes/portability-findings.md): Tracked issues discovered during the Go/Rust portability validation phase.

### Legacy
- [`legacy/encrypted_storage_key_management_spec.md`](./legacy/encrypted_storage_key_management_spec.md): The original integrated draft specification (Archived for reference).
