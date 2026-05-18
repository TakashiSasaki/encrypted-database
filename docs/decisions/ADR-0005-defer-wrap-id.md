# ADR 0005: Defer Decision on Dedicated `wrap_id`

## Status
Accepted

## Context
In `wrapped_key_tbl`, the current primary key is the composite `(wrapped_kid, wrapping_kid)`. This design implies that there can be at most one active wrapping relationship between a specific wrapped key and a specific wrapping key.

While simple, this limitation causes difficulties:
- Multiple generations of the same wrap (e.g., during safe migration, key rotation, KDF parameter upgrades) cannot easily coexist.
- Crash-safe rewrapping is harder because it relies on in-place updates.
- Per-wrap statuses (active, deprecated) and audit histories are constrained or lossy.
- Multi-provider or multi-device scenarios might need distinct wrap identities for the same logical key pair.

Introducing a dedicated UUIDv4 `wrap_id` as the primary key would solve these issues but adds complexity to the minimal design.

## Decision
The decision on whether to introduce a dedicated `wrap_id` is deferred.

The current schema will remain as `PRIMARY KEY (wrapped_kid, wrapping_kid)` until the necessity for multi-generational wraps, advanced multi-device synchronization, or complex AAD policy migrations makes the `wrap_id` strictly necessary.

## Consequences
- The database schema remains simpler in the short term.
- Safe re-wrapping logic requires careful transaction handling since in-place updates are required.
- Future work may require a schema migration to introduce `wrap_id` if the documented limitations become blockers.

## Related Files
- `docs/spec/open-questions.md` (Tracks this as an unresolved architectural consideration)
- `docs/backend/sqlite/schema.sql` (Maintains composite primary key)
- `docs/legacy/encrypted_storage_key_management_spec.md`