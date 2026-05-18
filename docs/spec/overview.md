# Overview

## Purpose
This specification defines the design for application-layer encryption, key hierarchies, key wrapping, unlock methods, recovery paths, and blind indexes for applications storing confidential data in local persistence layers such as SQLite.

The core design principle is to not rely solely on whole-database file encryption. Instead, the application encrypts confidential payloads as envelopes before storing them. Only non-secret metadata necessary for search, synchronization, and integrity management is kept in plaintext columns.

We borrow the concept from password managers like Bitwarden, where confidential fields are treated as encrypted representations, and metadata such as ID, timestamp, type, and synchronization metadata are kept separate. However, rather than adopting Bitwarden's specific `EncString` format as-is, we employ our own versioned envelopes assuming AEAD.

## Design Principles
1. Plaintext secret values, plaintext keys, master passwords, Shamir shares, and recovery codes are not stored in SQLite.
2. Confidential payloads are AEAD-encrypted with a `record_dek` or `file_dek`.
3. Payload encryption keys (`record_dek` / `file_dek`) are wrapped by higher-level keys for storage.
4. The entry point of the key hierarchy is called `unlock_kek`. The `unlock_kek` is obtained from multiple unlock providers, such as passphrase KDF, OS secret store, OS key handle, Shamir recovery, hardware token, or remote KMS.
5. The `unlock_kek` does not need to be singular. The same `database_kek` may be wrapped by multiple `unlock_kek`s.
6. `unlock_method` represents an abstract classification, `unlock_provider` represents a concrete implementation, and `unlock_kek_tbl` represents individual instance settings.
7. `provider_config_json` contains only provider-specific non-secret configurations. Values that exist on the master side, such as `provider`, `method`, and `platform`, are not duplicated.
8. AEAD Additional Authenticated Data (AAD) is used to bind the ciphertext to its storage context. The actual AAD byte sequence is generated deterministically within the library, and only the `aad_policy` is stored in the envelope or database.
9. Base64URL or BLOB storage formats are chosen based on the usage layer. BLOB columns are recommended internally in the DB, and JSON envelopes are recommended for API/file exchange.
10. JSON stored in SQLite, JSON used to generate AAD, and JSON serving as input for signatures, MACs, hashes, and UUID generation must always be canonicalized. The standard canonicalization method is the RFC 8785 JSON Canonicalization Scheme (JCS). Free-form JSON that is not subject to canonicalization is not stored.
