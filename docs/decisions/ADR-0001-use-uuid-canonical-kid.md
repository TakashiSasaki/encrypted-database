# ADR 0001: Use UUID Canonical String for Identifiers

## Status
Accepted (Updated)

## Context
The system requires identifiers for keys (`kid`), schemas, wraps, and objects. Earlier drafts of the specification included examples where `kid` values contained prefixes or encoded metadata about the key's type or purpose (e.g., `ulk-passphrase-argon2id-01`, `dbk-01972f2e...`, `dek-01972f3b...`). Furthermore, it was previously mandated that all identifiers strictly use UUID version 4.

Encoding meaning into identifiers creates problems during renaming, reclassification, migration, and UI changes. It also unnecessarily leaks metadata about the key structure within the identifier itself. Restricting identifiers solely to version 4 limits interoperability with newer or deterministic time-based standards (like UUIDv7).

## Decision
We will use stable, opaque UUID identifiers.

An identifier MUST be represented as a lowercase, hyphen-separated UUID canonical string:
`xxxxxxxx-xxxx-Mxxx-Nxxx-xxxxxxxxxxxx`
Where `M` is the version number (1 through 8) and `N` is the variant.

Identifiers MUST NOT encode meaning. They MUST NOT contain a human-readable prefix, key class, provider name, purpose, creation date, platform name, database name, or record type.

Key semantics MUST be stored in explicit metadata columns such as `key_class`, `purpose`, `alg`, `status`, `created_at_ms`, `unlock_provider`, `created_on_platform`, and `description_json`.

## Consequences
- Identifiers remain stable across schema or classification changes.
- Metadata leakage via identifiers is prevented.
- Normalization and querying become simpler and more uniform.
- Any existing code or examples using prefixed IDs must be updated.

## Related Files
- `docs/spec/terminology.md` (Defines canonical kid format)
- `docs/backend/sqlite/schema.sql` (Schema requires updating to enforce UUIDv4 if not already done)
- `docs/legacy/encrypted_storage_key_management_spec.md` (Contains older, superseded examples)