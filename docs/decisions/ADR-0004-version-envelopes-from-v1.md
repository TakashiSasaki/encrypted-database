# ADR 0004: Version Envelopes from the First Schema

## Status
Accepted

## Context
When designing storage formats for encrypted data and wrapped keys, it is common to overlook versioning until a breaking change is required, leading to brittle migrations and difficulty in supporting interoperability or testing across versions.

## Decision
The storage format is versioned from the beginning. Both external JSON envelopes and SQLite internal representations MUST include an envelope format version and an envelope type.

For JSON envelopes, fields `v` (e.g., `1`) and `type` (e.g., `aead`) are required.

For SQLite internal storage, tables containing wrapped keys or encrypted payloads must carry these versions explicitly.
- `encrypted_object_tbl` MUST have `envelope_v` and `envelope_type` columns.
- `wrapped_key_tbl` MUST have `envelope_v` and `envelope_type` columns.

## Consequences
- Schema migrations, algorithm agility, and parsing logic are explicitly supported from day one.
- Inferring version details from table shape is avoided, leading to more robust implementations.
- Storage footprint is slightly increased to accommodate the explicit version metadata.

## Related Files
- `docs/spec/envelope-format.md`
- `docs/backend/sqlite/schema.sql` (reflects these columns)
- `docs/legacy/encrypted_storage_key_management_spec.md`