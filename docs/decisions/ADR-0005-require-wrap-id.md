# ADR 0005: Require Dedicated `wrap_id`

## Status
Accepted (Updated)

## Context
In `wrapped_key_tbl`, the prior primary key was the composite `(wrapped_kid, wrapping_kid)`. This design implies that there can be at most one active wrapping relationship between a specific wrapped key and a specific wrapping key.

While simple, this limitation causes difficulties:
- Multiple generations of the same wrap (e.g., during safe migration, key rotation, KDF parameter upgrades) cannot easily coexist.
- Crash-safe rewrapping is harder because it relies on in-place updates.
- Per-wrap statuses (active, deprecated) and audit histories are constrained or lossy.
- Multi-provider or multi-device scenarios might need distinct wrap identities for the same logical key pair.

Introducing a dedicated UUIDv4 `wrap_id` as the primary key solves these issues. Initially deferred, the decision has been revisited and approved for immediate adoption to guarantee safe key rotation and future multi-device synchronization.

## Decision
A dedicated UUIDv4 `wrap_id` is required.

The schema MUST use `wrap_id` as the `PRIMARY KEY` for `wrapped_key_tbl`. The composite unique constraint on `(wrapped_kid, wrapping_kid)` is removed to allow multiple wrapping generations to coexist.

## Consequences
- Safe re-wrapping logic is simplified, allowing atomic INSERT followed by DELETE of the older generation.
- Multi-generational wraps and safe migrations are explicitly supported.
- `wrap_id` must be generated as a UUIDv4 and validated.

## Related Files
- `docs/backend/sqlite/schema.sql` (Now updated to use `wrap_id` as primary key)
- `docs/legacy/encrypted_storage_key_management_spec.md`