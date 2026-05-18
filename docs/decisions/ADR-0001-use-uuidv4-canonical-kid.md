# ADR 0001: Use UUIDv4 Canonical String for Key Identifiers (`kid`)

## Status
Accepted

## Context
The system requires identifiers for keys (`kid`). Earlier drafts of the specification included examples where `kid` values contained prefixes or encoded metadata about the key's type or purpose (e.g., `ulk-passphrase-argon2id-01`, `dbk-01972f2e...`, `dek-01972f3b...`).

Encoding meaning into identifiers creates problems during renaming, reclassification, migration, and UI changes. It also unnecessarily leaks metadata about the key structure within the identifier itself.

## Decision
We will use stable, opaque UUIDv4 identifiers for `kid`.

A `kid` MUST be represented as a lowercase, hyphen-separated UUIDv4 canonical string:
`xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx` (where `y` is one of 8, 9, a, or b).

A `kid` MUST NOT encode meaning. It MUST NOT contain a human-readable prefix, key class, provider name, purpose, creation date, platform name, database name, or record type.

Key semantics MUST be stored in explicit metadata columns such as `key_class`, `purpose`, `alg`, `status`, `created_at_ms`, `unlock_provider`, `created_on_platform`, and `description_json`.

## Consequences
- Identifiers remain stable across schema or classification changes.
- Metadata leakage via identifiers is prevented.
- Normalization and querying become simpler and more uniform.
- Any existing code or examples using prefixed IDs must be updated.

## Related Files
- `docs/encrypted_storage_key_management_spec.md` (Contains older, superseded examples)
- `docs/schema.sql` (Schema requires updating to enforce UUIDv4 if not already done)