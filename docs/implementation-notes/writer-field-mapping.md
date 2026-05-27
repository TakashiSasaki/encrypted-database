# Storage Format V1 Writer Field Mapping Audit

This document tracks how each field in the Storage Format V1 SQLite schema is handled by the baseline implementations (Python / Node.js) and the portability scaffold writers (Go / Rust).

## Definitions

*   **populated by writer**: Actively written by the implementation (with dynamic values).
*   **derived by writer**: Computed from other values (e.g., AAD generated from context).
*   **generated random value**: Created using a CSRNG (e.g., UUIDs, nonces, salt).
*   **generated deterministic metadata**: Constant or context-specific values (e.g., library name).
*   **copied from API input**: Directly taken from caller arguments (e.g., `passphrase`, `platform`, `schema_uuid`).
*   **copied from schema/default**: Taken from schema definitions or static values (e.g., `1` for `envelope_v`).
*   **validated only**: Read or constrained, but not directly populated.
*   **preserved for future feature**: Set to default/null for future use.
*   **not used by minimal writer**: Completely ignored in current minimal scaffold scope.
*   **intentionally left absent**: Explicitly ignored or set to NULL due to unsupported features (e.g., key lifecycle).

## Field Mapping

### `storage_metadata_tbl`

| Field | Source | Python/Node | Go/Rust | Notes |
|---|---|---|---|---|
| `property` | populated by writer | populated | populated | Keys for metadata properties. |
| `value` | generated deterministic metadata, generated random value | populated | populated | Contains format ID, db UUID, library versions, timestamp, features (`[]`). Go/Rust output `"vault-go"` / `"vault-rust"` and `"0.0.0-dev"`. |

### `key_class_tbl`, `key_profile_tbl`, `unlock_method_tbl`, `unlock_provider_tbl`, `platform_tbl`, `unlock_provider_platform_tbl`

These tables contain static seed data populated during schema initialization.
*   **All fields**: `copied from schema/default` (Seed data). Writers only validate against these tables (e.g., `platform` validation).

### `key_tbl`

| Field | Source | Python/Node | Go/Rust | Notes |
|---|---|---|---|---|
| `kid` | generated random value | generated v4 UUID | generated v4 UUID | Must be lowercase canonical. |
| `key_class` | generated deterministic metadata | populated | populated | `unlock_kek`, `database_kek`, `record_dek` |
| `purpose` | generated deterministic metadata | populated | populated | `wrap_database_keys`, `wrap_record_keys`, `encrypt_payload` |
| `alg` | copied from schema/default | populated | populated | `A256GCM` |
| `status` | copied from schema/default | populated | populated | Set to `active`. Other values (`decrypt_only`, etc.) are ignored. |
| `created_at_ms` | generated deterministic metadata | populated | populated | Current time in MS |
| `activated_at_ms` | intentionally left absent | absent (NULL) | absent (NULL) | Key lifecycle (delayed activation) not supported. |
| `deactivated_at_ms` | intentionally left absent | absent (NULL) | absent (NULL) | Key lifecycle (rotation) not supported. |
| `destroyed_at_ms` | intentionally left absent | absent (NULL) | absent (NULL) | Key lifecycle (destruction) not supported. |
| `description_json` | intentionally left absent | absent (NULL) | absent (NULL) | Not supported in minimal writer. |

### `unlock_kek_tbl`

| Field | Source | Python/Node | Go/Rust | Notes |
|---|---|---|---|---|
| `kid` | generated random value | populated | populated | References `key_tbl`. |
| `unlock_provider` | generated deterministic metadata | populated | populated | `passphrase_argon2id` |
| `provider_config_json` | derived by writer | populated | populated | Contains salt (base64url) and Argon2id config in canonical JCS. |
| `device_id` | intentionally left absent | absent (NULL) | absent (NULL) | Not supported. |
| `created_on_platform` | copied from API input | populated | populated | Must match `platform_tbl`. |

### `wrapped_key_tbl`

| Field | Source | Python/Node | Go/Rust | Notes |
|---|---|---|---|---|
| `wrap_id` | generated random value | generated v4 UUID | generated v4 UUID | |
| `wrapped_kid` | generated random value | populated | populated | References `key_tbl`. |
| `wrapping_kid` | generated random value | populated | populated | References `key_tbl`. |
| `envelope_v` | copied from schema/default | `1` | `1` | |
| `envelope_type` | copied from schema/default | `key_wrap` | `key_wrap` | |
| `wrap_alg` | copied from schema/default | `A256GCM` | `A256GCM` | |
| `nonce` | generated random value | 12 bytes | 12 bytes | |
| `wrapped_key` | derived by writer | populated | populated | AES-GCM output (ciphertext \|\| tag). |
| `aad_policy` | derived by writer | populated | populated | `wrap-database-key-v1` or `wrap-record-key-v1`. |
| `created_at_ms` | generated deterministic metadata | populated | populated | Current time in MS |

### `encrypted_object_tbl`

| Field | Source | Python/Node | Go/Rust | Notes |
|---|---|---|---|---|
| `object_uuid` | generated random value | generated v4 UUID | generated v4 UUID | |
| `envelope_v` | copied from schema/default | `1` | `1` | |
| `envelope_type` | copied from schema/default | `aead` | `aead` | |
| `schema_uuid` | copied from API input | populated | populated | Validated as canonical UUID. |
| `content_type` | copied from API input | populated | populated | Validated to contain `/`. |
| `alg` | copied from schema/default | `A256GCM` | `A256GCM` | |
| `kid` | generated random value | populated | populated | References `key_tbl` (`record_dek`). |
| `nonce` | generated random value | 12 bytes | 12 bytes | |
| `ciphertext` | derived by writer | populated | populated | AES-GCM output (ciphertext \|\| tag). |
| `aad_policy` | derived by writer | populated | populated | `record-payload-v1` |
| `created_at_ms` | generated deterministic metadata | populated | populated | Current time in MS |
| `updated_at_ms` | generated deterministic metadata | populated | populated | Same as `created_at_ms` (no updates supported yet). |

## Summary

The Go and Rust writers currently behave consistently with the baseline Python and Node.js implementations. They correctly exclude unsupported fields (such as key lifecycle timestamps and `device_id`) and safely map API inputs, generated IDs, and deterministic values where required by the V1 schema.
