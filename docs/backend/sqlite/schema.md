# SQLite Schema

This document provides a conceptual overview of the authoritative `schema.sql` file. The schema enforces the relational model for the key hierarchy, providers, and encrypted objects.

## Key Management Tables

- **`key_class_tbl`**: Defines the valid classes of keys (e.g., `unlock_kek`, `database_kek`, `record_dek`).
- **`key_profile_tbl`**: Defines allowable combinations of key class, purpose, and algorithm.
- **`key_tbl`**: The central registry of all keys. It stores metadata, status, and UUIDv4 `kid`s. It does not store key material.
- **`wrapped_key_tbl`**: Stores keys that are wrapped by other keys (e.g., a `database_kek` wrapped by an `unlock_kek`, or a `record_dek` wrapped by a `database_kek`). It contains the wrapping algorithm, nonce, the wrapped bytes (`wrapped_key`), and the `aad_policy`.
- **`unlock_kek_tbl`**: Stores configuration for entry-point `unlock_kek` instances, linking them to specific unlock providers and the concrete platform on which they were created.

## Object Storage Table

- **`encrypted_object_tbl`**: Stores the actual encrypted payloads. It contains the object's UUID, the schema/content-type metadata, the `kid` of the `record_dek` used to encrypt it, the nonce, the ciphertext, and the `aad_policy`.

## Provider and Platform Tables

- **`unlock_method_tbl`**: Abstract methods for unlocking (e.g., `passphrase_kdf`).
- **`unlock_provider_tbl`**: Concrete implementations of unlock methods (e.g., `passphrase_argon2id`).
- **`platform_tbl`**: A registry of supported concrete deployment platforms (`linux`, `windows`, `macos`, `ios`, `android`, `web`, `server`, `cloud`).
- **`unlock_provider_platform_tbl`**: The many-to-many relationship mapping which providers are supported on which platforms.

The canonical schema enforces referential integrity across these entities using strict Foreign Key constraints.
