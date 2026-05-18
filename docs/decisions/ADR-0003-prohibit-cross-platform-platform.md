# ADR 0003: Prohibit `cross_platform` as a Concrete Platform Name

## Status
Accepted

## Context
The system maps unlock providers to platforms to define where and how they are supported. Previously, the label `cross_platform` was used or discussed as a way to indicate that a method (like passphrase KDF or Shamir recovery) was not bound to a specific OS.

However, `cross_platform` is ambiguous. It conflates algorithm portability, testing environments, unspecified platforms, and actual deployment environments.

## Decision
The string `cross_platform` is prohibited as a concrete platform name.

Every unlock provider instance MUST record a concrete platform name in `unlock_kek_tbl.created_on_platform`. This value MUST reference a specific, concrete entry in `platform_tbl(platform)` (e.g., `windows`, `macos`, `linux`, `android`, `ios`, `web`, `server`). It MUST NOT be NULL and MUST NOT be `cross_platform`.

A conceptually portable provider (like `passphrase_argon2id`) MUST be explicitly mapped to each concrete platform it supports via repeated rows in the mapping table, rather than relying on an abstract label.

## Consequences
- Removes ambiguity about where a provider is actually supported and deployed.
- Simplifies logic by ensuring all platforms are concrete environments.
- Requires updates to any draft text, tests, or initializations that rely on the `cross_platform` concept or omit platform names entirely.

## Related Files
- `docs/encrypted_storage_key_management_spec.md`
- `docs/schema.sql`