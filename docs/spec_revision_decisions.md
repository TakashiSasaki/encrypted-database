# Specification Revision Decisions

This document records resolved design decisions that supersede inconsistent examples or older draft text in `docs/encrypted_storage_key_management_spec.md`.

## 1. Stable key identifiers

`kid` is an opaque UUIDv4 identifier.

A `kid` MUST be represented as a lowercase, hyphen-separated UUIDv4 canonical string:

```text
xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
```

where `y` is one of `8`, `9`, `a`, or `b`.

A `kid` MUST NOT encode meaning. It MUST NOT contain a human-readable prefix, key class, provider name, purpose, creation date, platform name, database name, or record type.

The following forms are invalid as `kid` values:

```text
ulk-passphrase-argon2id-01
dbk-01972f2e-4b51-7a11-8a2f-8a4f0db0a101
dek-01972f3b-77c8-7a8d-b9a7-2eac8f2d9912
```

Key semantics MUST be stored in explicit metadata columns such as `key_class`, `purpose`, `alg`, `status`, `created_at_ms`, `unlock_provider`, `created_on_platform`, and `description_json`.

Rationale: identifiers should remain stable across renaming, reclassification, migration, and UI changes. Encoding meaning in `kid` creates metadata leakage and makes later normalization difficult.

## 2. JSON canonicalization

All JSON values that are persisted, authenticated, hashed, MACed, signed, indexed, or used as UUID/hash input MUST be canonicalized according to RFC 8785 JSON Canonicalization Scheme (JCS).

This includes at least:

- `description_json`
- `aad_context_json`
- `provider_config_json`
- plaintext JSON payload before encryption
- blind-index input values represented as JSON
- future signature, MAC, hash, or UUID input JSON
- test vector JSON values whose bytes are compared across implementations

Implementations MUST NOT treat `json.dumps(..., sort_keys=True)` or a simple recursive key-sort plus `JSON.stringify()` as automatically equivalent to JCS. Those techniques may be useful implementation steps, but they are insufficient unless the complete RFC 8785 requirements are satisfied.

If an implementation language lacks a suitable JCS library, the implementation MUST provide its own JCS-compatible canonicalizer and test it against shared test vectors.

Rationale: AAD, HMAC, hash, UUID, and cross-language test vectors depend on byte identity, not only semantic JSON equivalence. Python and Node.js default JSON serializers can differ in Unicode escaping, number serialization, object key ordering details, and edge-case handling.

## 3. Concrete platform names only

`cross_platform` is prohibited.

Every unlock provider instance MUST record a concrete platform name in `unlock_kek_tbl.created_on_platform`. This value MUST reference `platform_tbl(platform)`. It MUST NOT be NULL and MUST NOT be `cross_platform`.

A provider that is conceptually portable, such as `passphrase_argon2id`, MUST be represented by explicit provider-platform rows:

```text
(passphrase_argon2id, windows)
(passphrase_argon2id, macos)
(passphrase_argon2id, linux)
(passphrase_argon2id, server)
(passphrase_argon2id, web)
(passphrase_argon2id, android)
(passphrase_argon2id, ios)
```

The fact that the algorithm is portable is expressed by repeated concrete mappings, not by an abstract platform label.

Rationale: `cross_platform` is ambiguous. It can mean algorithm portability, test environment, no platform binding, unspecified platform, or unsupported deployment. These meanings must not be conflated.

## 4. Versioned envelopes from the first schema

The storage format is versioned from the beginning. Versioning is not an afterthought.

Both external JSON envelopes and SQLite internal representations MUST include an envelope format version and an envelope type.

For encrypted payloads, the standard version-1 JSON envelope is:

```json
{
  "v": 1,
  "type": "aead",
  "alg": "A256GCM",
  "kid": "550e8400-e29b-41d4-a716-446655440000",
  "nonce": "base64url-no-padding",
  "ct": "base64url-no-padding",
  "aad_policy": "record-payload-v1"
}
```

For SQLite internal storage, `encrypted_object_tbl` MUST carry the corresponding version and type as explicit columns, such as:

```sql
envelope_v INTEGER NOT NULL DEFAULT 1 CHECK (envelope_v >= 1),
envelope_type TEXT NOT NULL DEFAULT 'aead' CHECK (envelope_type IN ('aead'))
```

For wrapped keys, `wrapped_key_tbl` MUST likewise carry explicit version and type columns, such as:

```sql
envelope_v INTEGER NOT NULL DEFAULT 1 CHECK (envelope_v >= 1),
envelope_type TEXT NOT NULL DEFAULT 'key_wrap' CHECK (envelope_type IN ('key_wrap'))
```

Rationale: schema migration, interoperability, test vectors, and future algorithm agility all require the stored representation to say what format it uses. Inferring version from table shape alone makes migration brittle.

## 5. Section numbering policy

The main specification should be renumbered so that headings are monotonic and unique. Nested headings must match their parent section. In particular, the current duplicated or stale numbering around provider configuration examples, operational scenarios, blind index, and security sections should be corrected.

A proposed top-level numbering is:

1. Purpose
2. Design principles
3. Terminology
4. Key hierarchy
5. Encrypted envelopes
6. SQLite schema
7. Unlock methods, providers, and platforms
8. Platform classification
9. Provider classification
10. Provider configuration JSON
11. Operational scenarios
12. Search and blind indexes
13. Security specification
14. Portability and test vectors
15. Implementation checklist
16. Resolved and open issues

## 6. `wrap_id` deferred decision

Whether `wrapped_key_tbl` needs a dedicated `wrap_id` remains deferred. The current schema still uses:

```sql
PRIMARY KEY (wrapped_kid, wrapping_kid)
```

This means the model permits at most one current row for a given wrapped key and wrapping key pair.

The following risks and limitations should be considered before deciding whether to introduce `wrap_id`.

### 6.1 Multiple generations of the same wrap pair cannot coexist

Without `wrap_id`, rewrapping the same `wrapped_kid` by the same `wrapping_kid` overwrites or conflicts with the existing row. This makes it hard to retain both the old and new wrapped material during a safe migration.

This matters when KDF parameters change, AAD policy changes, envelope version changes, nonce/tag representation changes, or the wrapping algorithm changes while the logical key pair remains the same.

### 6.2 Crash-safe rewrap is harder

A safe rewrap often wants the following sequence:

1. Insert a new wrap row.
2. Verify that the new row can unwrap successfully.
3. Mark the old row as inactive or decrypt-only.
4. Later delete or destroy the old wrapped material.

With `PRIMARY KEY (wrapped_kid, wrapping_kid)`, step 1 cannot be expressed without updating the existing row in place. In-place update narrows the recovery window: if the transaction or application fails at the wrong point, it is harder to know whether the old or new wrap is the reliable one.

SQLite transactions reduce this risk, but they do not remove the modeling limitation. The database cannot represent two candidate wraps for the same pair.

### 6.3 Per-wrap status cannot be modeled cleanly

Key status belongs to `key_tbl`, but a wrap row has its own lifecycle. One unlock path may be active, another may be deprecated, and another may be retained only for recovery.

Without `wrap_id`, status such as `active`, `decrypt_only`, `disabled`, `superseded`, or `destroyed` can only be attached awkwardly to the `(wrapped_kid, wrapping_kid)` pair. It cannot distinguish generations of the same pair.

### 6.4 Audit history is lossy

If each pair has only one row, replacing a wrap row loses the prior nonce, wrapped bytes, AAD policy, creation time, and envelope version unless a separate audit/event table captures them.

That may be acceptable for a minimal implementation, but it weakens forensic reconstruction and migration debugging.

### 6.5 AAD policy migration becomes constrained

AAD policies such as `wrap-database-key-v1` and `wrap-record-key-v1` may evolve. Without `wrap_id`, the same logical pair cannot have both the old and new AAD-bound wrapped material in the same table.

That makes gradual migration and mixed-version readers more difficult.

### 6.6 Multi-provider or multi-device semantics can become ambiguous

The pair `(wrapped_kid, wrapping_kid)` assumes the wrapping key instance is enough to identify the wrap. That may be true for simple exported-key providers.

For non-exportable key handles, remote KMS, hardware tokens, or escrow services, the same logical wrapping key may need multiple provider-specific wrap artifacts, policy contexts, or device-specific handles. A separate `wrap_id` gives each artifact its own identity.

### 6.7 Replication and conflict resolution are weaker

In a replicated or eventually synchronized database, two peers might independently rewrap the same key pair. Without `wrap_id`, both peers write the same primary key and create an update conflict. With `wrap_id`, both rows can coexist until policy decides which one is active.

This is especially relevant if the database is later synchronized across devices.

### 6.8 When `wrap_id` may be unnecessary

A separate `wrap_id` may be unnecessary if the design intentionally keeps only one wrap row per key pair, does not preserve wrap history, performs rewrap atomically in a single local SQLite transaction, has no multi-device concurrent mutation, and treats old wrapped material as disposable after successful replacement.

That minimal design is simpler, but it should be documented as a deliberate trade-off.

### 6.9 Likely schema if `wrap_id` is adopted later

A future schema could use a UUIDv4 `wrap_id` as the primary key:

```sql
CREATE TABLE wrapped_key_tbl (
    wrap_id TEXT PRIMARY KEY,
    wrapped_kid TEXT NOT NULL,
    wrapping_kid TEXT NOT NULL,
    envelope_v INTEGER NOT NULL,
    envelope_type TEXT NOT NULL,
    wrap_alg TEXT NOT NULL,
    nonce BLOB NOT NULL,
    wrapped_key BLOB NOT NULL,
    aad_policy TEXT NOT NULL,
    aad_context_json TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('active', 'decrypt_only', 'disabled', 'superseded', 'destroyed')),
    created_at_ms INTEGER NOT NULL,
    deactivated_at_ms INTEGER,
    destroyed_at_ms INTEGER,
    FOREIGN KEY (wrapped_kid) REFERENCES key_tbl(kid),
    FOREIGN KEY (wrapping_kid) REFERENCES key_tbl(kid)
);
```

A partial unique index could enforce at most one active row for a pair:

```sql
CREATE UNIQUE INDEX wrapped_key_one_active_pair_idx
ON wrapped_key_tbl (wrapped_kid, wrapping_kid)
WHERE status = 'active';
```

This gives each wrap artifact an immutable identity while still preserving the policy that only one active wrap should normally exist for a given pair.
