# Encrypted Database Documentation

This directory contains the documentation, specifications, and architectural decisions for the Encrypted Database project.

## Table of Contents

- [How to Read the Docs](#how-to-read-the-docs)
- [Canonical Sources](#canonical-sources)
- [Existing Documents](#existing-documents)
  - [Main Specifications](#main-specifications)
  - [Architecture Decision Records (ADRs)](#architecture-decision-records-adrs)
  - [Implementation Notes](#implementation-notes)

## How to Read the Docs

For future contributors, please read the documentation in the following order:
1. Start with this **README** to understand the documentation structure.
2. Review the **Architecture Decision Records (ADRs)** in `docs/decisions/` to understand the resolved design decisions and foundational rules.
3. Check `docs/spec_revision_decisions.md` for historical context on recent changes.
4. Read the **Main Draft Specification** (`docs/encrypted_storage_key_management_spec.md`) to grasp the overall architecture, but keep in mind that some of its text is older and superseded by the ADRs and concrete schema.
5. Refer to `docs/schema.sql` as the absolute truth for the current SQLite database structure.
6. Check `docs/spec/open-questions.md` and `docs/implementation-notes/implementation-gaps.md` for ongoing design work and areas where implementations are still catching up to the spec.

## Canonical Sources

The documentation is currently undergoing a phased refactoring. Because of this, there are overlapping sources of truth. Please use the following precedence rules:

- **Schema Truth**: `docs/schema.sql` is currently the concrete, canonical SQLite schema source. It reflects newer decisions than some of the older SQL snippets found in the main draft.
- **Decision Truth**: The ADRs in `docs/decisions/` and `docs/spec_revision_decisions.md` supersede any inconsistent older draft text in the main specification.
- **Main Draft**: `docs/encrypted_storage_key_management_spec.md` is still an integrated draft. It contains valuable architectural overview but still has some stale examples (e.g., prefixed `kid` examples, `cross_platform` discussion) that are explicitly overridden by newer decisions.

## Existing Documents

### Main Specifications

- [`encrypted_storage_key_management_spec.md`](./encrypted_storage_key_management_spec.md): The integrated draft specification for key management and encrypted storage. (Note: Contains some stale examples).
- [`schema.sql`](./schema.sql): The canonical, concrete SQLite schema.
- [`spec_revision_decisions.md`](./spec_revision_decisions.md): Records resolved design decisions that override the older draft text.
- [`spec_issues_report.md`](./spec_issues_report.md): Implementation issue report.
- [`argon2id_defaults.md`](./argon2id_defaults.md): Standard Argon2id default parameters.
- [`spec/open-questions.md`](./spec/open-questions.md): Extracted unresolved design questions and ongoing considerations.

### Architecture Decision Records (ADRs)

- [`decisions/README.md`](./decisions/README.md): Index of Architecture Decision Records.
- [`decisions/ADR-0001-use-uuidv4-canonical-kid.md`](./decisions/ADR-0001-use-uuidv4-canonical-kid.md): Stable key identifiers.
- [`decisions/ADR-0002-require-rfc8785-jcs.md`](./decisions/ADR-0002-require-rfc8785-jcs.md): JSON canonicalization.
- [`decisions/ADR-0003-prohibit-cross-platform-platform.md`](./decisions/ADR-0003-prohibit-cross-platform-platform.md): Concrete platform names.
- [`decisions/ADR-0004-version-envelopes-from-v1.md`](./decisions/ADR-0004-version-envelopes-from-v1.md): Versioned envelopes from the first schema.
- [`decisions/ADR-0005-defer-wrap-id.md`](./decisions/ADR-0005-defer-wrap-id.md): Deferral of dedicated wrap ID in the schema.

### Implementation Notes

- [`implementation-notes/implementation-gaps.md`](./implementation-notes/implementation-gaps.md): Known gaps between the canonical specifications and the current implementations.
