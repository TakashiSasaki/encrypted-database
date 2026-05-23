# Storage Format V1 Core (Draft)

```text
Status: Draft
Compatibility: pre-v1, no production compatibility guarantee
Implementation status: Python partial, Node.js partial, browser-test partial, Go planned, Rust planned
Normative status: Proposed storage-format-v1 candidate
```

## 1. Purpose and Scope
This document specifies the language-independent and DBMS-independent logical layout for the Encrypted Database storage format. The storage format defines how encrypted payloads, metadata, key material, and provider configurations are structured. It establishes invariant cryptographic formats, encoding rules, and key hierarchies required for interoperability across Python, Node.js, Web Browser, Go, and Rust implementations.

This is the Storage Format Core. Physical representations (e.g., SQLite files) are specified in separate profile documents (e.g., `storage-format-sqlite.md`).

### 1.1 Core vs. SQLite Profile Responsibility Boundaries
To maintain a clean separation of concerns, the boundaries are strictly defined:

*   **Storage Format Core**: Defines UUID canonical format, key hierarchy, AEAD layout, JCS normalization, AAD reconstruction rules, provider config semantics, payload value models, and feature/versioning policies. (e.g., "UUID must be lowercase hyphenated canonical string").
*   **SQLite Storage Profile**: Defines the physical tables, columns, column types, CHECK constraints, PRAGMAs, `json_valid` usage, foreign keys, transaction behavior, and the canonical `schema.sql`. (e.g., "SQLite uses GLOB CHECK to help enforce UUID shape").

## 2. Format Stability Model
Before the V1 stabilization is officially declared, this format is considered **experimental (pre-v1)**. Destructive schema changes, backwards-incompatible cryptographic modifications, and structural alterations are permitted without migration pathways.

After V1 stabilization, the format guarantees backward compatibility. Any structural or cryptographic changes must conform to the Versioning and Compatibility Policy and Migration Policy defined below.

## 3. Storage Format Identity
A storage file must contain metadata to identify its format, version, and origin. This ensures that implementations can correctly identify and read the structure. The identity is managed via both database metadata and PRAGMAs (in SQLite).

Components for Storage Format Identity include:
*   **`PRAGMA application_id` (SQLite)**: Used as a magic number indicating that this file is a `vault.moukaeritai.work` storage format database.
*   **`PRAGMA user_version` (SQLite)**: Used as an auxiliary integer tracking the SQLite schema / migration version.
*   **`storage_format_id`**: A fixed string identifying the logical database format.
*   **`format_major`**: Major version number (e.g., 1). Changes indicate logical storage format compatibility breaks. (Separated from `schema_version`).
*   **`format_minor`**: Minor version number (e.g., 0). Changes indicate backward-compatible logical additions, combined with feature flags.
*   **`schema_version`**: An integer representing the specific underlying schema layout (e.g., SQLite DDL / migration step). The `PRAGMA user_version` should generally synchronize with this value.
*   **`database_uuid`**: A canonical UUID uniquely identifying this specific database instance. Initialized via UUIDv4.
*   **`created_at_ms`**: Unix timestamp in milliseconds indicating when the database was created.
*   **`created_by_library`**: A string indicating the library implementation that created the database (e.g., `"python-vault"`, `"nodejs-vault"`). Note that the library version and storage format version are fundamentally separate.
*   **`created_by_version`**: The version string of the library that created the database.
*   **`required_features`**: A JCS canonical JSON array of feature flags that a reader MUST understand.
*   **`optional_features`**: A JCS canonical JSON array of feature flags that a reader MAY understand.

*Note: Schema Hash / Schema Fingerprint has been deferred to future hardening.*

## 4. Versioning and Compatibility Policy
This policy outlines how implementations handle versioning and feature flags for V1:

*   **Pre-V1 Databases**: Implementations of V1 MUST explicitly reject opening databases that lack V1 metadata/versioning structures (pre-v1 databases). Since no production databases exist yet, pre-V1 compatibility is not guaranteed.
*   **Format Major Mismatch**: If the `format_major` of the database is unknown or greater than the implementation's supported major version, the implementation MUST reject opening the database.
*   **Format Minor Mismatch**: If the `format_minor` of the database is greater than the implementation's supported minor version, the implementation MAY attempt to open it, provided no unknown features are present.
*   **Unknown Features (Required or Optional)**: If the database contains any feature flag not implemented by the reader (whether in `required_features` or `optional_features`), the implementation MUST safely default to rejecting the open operation. V1 does not support read-only fallback for unknown optional features; this is deferred as a future enhancement.
*   **Destructive Changes**: V1 stabilization prohibits destructive changes without an explicit migration policy.

## 5. Database Identity and Metadata
Every initialized database possesses a single identity encompassing the identity components described in Section 3. The identity information must be stored in a dedicated key-value metadata table (`storage_metadata_tbl`). See the SQLite profile for the exact table definition.

## 6. Key Hierarchy
The storage format employs an envelope encryption model with the following key classes:

1.  **`unlock_kek`**: The top-level Key Encryption Key. Derived from a passphrase KDF (Argon2id), an OS secret store, or another unlock provider. It is used to wrap and unwrap the `database_kek`.
2.  **`database_kek`**: A Key Encryption Key used to wrap data-encryption keys (`record_dek`, `file_dek`).
3.  **`workspace_kek`**: (Optional) A Key Encryption Key utilized for sharing or project boundary separation. Wraps `record_dek`s.
4.  **`record_dek`**: The Data Encryption Key utilized for encrypting individual JSON payloads (records).
5.  **`file_dek`**: The Data Encryption Key utilized for encrypting binary blobs or large files.
6.  **`index_key`**: A key used for deterministic keyed operations, such as HMAC-based blind search indexes.

Key material plaintext is never stored at rest. Keys wrap other keys using the standardized Key-Wrap Layout. The storage format tracks key statuses conceptually (e.g., `active`, `decrypt_only`, `disabled`, `destroyed`).

## 7. Unlock Providers and Provider Config
Unlock providers govern the derivation or retrieval of the `unlock_kek`. The primary provider is `passphrase_argon2id`.

*   **Provider Config JSON**: To accommodate different KDF parameters or future providers, each `unlock_kek` record stores a `provider_config_json`.
*   **Storage Representation**: The provider config must be stored as a strictly JCS-canonicalized JSON string.
*   **Provider Config Explicitness**: The configuration object MUST explicitly store all necessary fields to fully describe the operation. For `passphrase_argon2id`, it must contain:
    ```json
    {
      "kdf": "argon2id",
      "profile": "argon2id-profile-v1",
      "salt": "...",
      "memory_kib": 65536,
      "iterations": 3,
      "parallelism": 1,
      "output_bytes": 32
    }
    ```
    *   `salt` MUST be a base64url encoded string (without padding).
*   **Argon2id Profile V1 Immutable Definition**: The `argon2id-profile-v1` defines immutable parameters (`memory_kib=65536`, `iterations=3`, `parallelism=1`, `salt_bytes=16`, `output_bytes=32`). Implementations MUST use these exact parameters for new database initialization.
*   **Unlock Validation**: Unlock operations dynamically read parameters from `provider_config_json`. If the explicit parameters contradict the immutable definition of `profile="argon2id-profile-v1"`, or if the decoded length of the `salt` does not exactly match `salt_bytes` (16 bytes), the database is considered invalid and unlock MUST be rejected.

## 8. AEAD Envelope Layout
All encrypted data (both keys and payloads) utilizes an invariant Authenticated Encryption with Associated Data (AEAD) layout.

*   **AEAD Algorithm**: `AES-256-GCM` (A256GCM).
*   **Nonce Length**: Strictly 12 bytes.
*   **Tag Length**: Strictly 16 bytes.
*   **Ciphertext Storage**: Encrypted bytes are stored as the concatenation of `ciphertext || tag`.
*   **Nonce Storage**: The nonce is stored as a distinct field/column, explicitly separate from the ciphertext.
*   **Randomization**: Production paths MUST use Cryptographically Secure Pseudorandom Number Generators (CSPRNG) for the 12-byte nonces. Fixed nonces are exclusively reserved for static test vectors.

## 9. Key-Wrap Layout
The wrapping of one key by another (e.g., `database_kek` wrapping a `record_dek`) follows the standard AEAD Envelope Layout.

*   **Algorithm**: `A256GCM`.
*   **Ciphertext**: The encrypted raw 32-byte key material + 16-byte authentication tag.
*   **AAD Context**: The `aad_context_json` is deliberately NOT stored in the database. Implementations MUST reconstruct the AAD bytes deterministically based on the `aad_policy`, the `wrapped_kid`, and the `wrapping_kid`.

## 10. Payload Encryption Layout
The encryption of application data records follows the standard AEAD Envelope Layout.

*   **Algorithm**: `A256GCM`.
*   **Plaintext**: The payload plaintext is the UTF-8 bytes of the strict JCS-canonicalized JSON representation of the payload.
*   **Ciphertext**: The encrypted canonical JSON bytes + 16-byte authentication tag.
*   **AAD Context**: The `aad_context_json` is NOT stored. Implementations MUST reconstruct the AAD bytes deterministically based on the `aad_policy` and required identity fields (e.g., `object_uuid`, `schema_uuid`).

## 11. AAD Reconstruction Rules
To prevent metadata tampering without bloating storage, AAD bytes are computed dynamically.

*   **No Explicit Storage**: The `aad_context_json` is not stored. The database stores the `aad_policy` name and necessary metadata identifiers.
*   **Reconstruction**: Each implementation MUST deterministically reconstruct the AAD JSON object based on the `aad_policy`.
*   **Canonicalization**: The AAD bytes used in the AES-GCM primitive MUST be the UTF-8 bytes of the JCS-canonicalized AAD JSON object.
*   **Policy Names**: AAD policy names MUST exactly match shared specifications and test vectors. Representative examples:
    *   `wrap-database-key-v1`
    *   `wrap-record-key-v1`
    *   `record-payload-v1`
*   **Validation**: Implementations MUST validate their reconstruction against the shared AAD machine-readable test vectors.

## 12. JCS Canonicalization Rules
The storage format relies on strict JSON Canonicalization Scheme (RFC 8785) for ALL JSON stored in the database. There are no exceptions.

*   **All JSON Columns**: Any column suffixed with `_json` MUST contain JCS canonical JSON text.
*   **Feature Flags**: The `required_features` and `optional_features` arrays stored in the metadata table MUST be JCS canonical JSON arrays (e.g., `[]`, `["blind_index_v1"]`).
*   **Payload Encryption**: The plaintext input to the payload encryption cipher MUST be the JCS-canonicalized bytes of the payload JSON.
*   **Provider Config**: The `provider_config_json` stored in the database MUST be JCS-canonicalized.
*   **AAD Context**: The AAD bytes input to the AES-GCM cipher MUST be the JCS-canonicalized bytes of the reconstructed AAD context object.
*   **No Native Serializers**: Implementations MUST NOT use standard language-native JSON serializers (e.g., `json.dumps()`, `JSON.stringify()`) for these cryptographic boundaries or DB insertion, as they do not guarantee RFC 8785 compliance.
*   **Validation**: While SQLite `json_valid()` performs basic structural checks, true JCS canonicality MUST be guaranteed by the application layer and conformance tests.

## 13. Payload Value Model
The storage format imposes strict constraints on the shape of payload records.

*   **Top-Level**: The top-level payload MUST be a JSON object (dictionary).
*   **Nested Types**: Nested values are strictly limited to valid JSON-compatible types:
    *   Object
    *   Array
    *   String
    *   Finite Number
    *   Boolean
    *   Null
*   **Binary Rejection**: Raw binary representations (e.g., `Buffer`, `bytes`, `ArrayBuffer`) are explicitly rejected at any depth. Consumers wishing to store binary data must encode it as a string (e.g., base64url).
*   **Non-JSON Rejection**: Types outside the strict JSON specification (e.g., `NaN`, `Infinity`, `Set`, `Map`, `Date`) are explicitly rejected.
*   **Numeric Portability**: Numeric types present known portability issues between 64-bit IEEE 754 floats (JavaScript), arbitrary precision integers (Python), and strict typing (Go/Rust). (Draft Gap: A "safe integer policy" is not yet finalized for V1).

## 14. Feature Flags
To support safe, backward-compatible upgrades, the format uses a feature flag array system stored in the metadata.
*   All feature flag arrays MUST be strictly stored as JCS canonical JSON strings containing arrays of strings.
*   In the initial Storage Format V1 release, the only permitted value for both `required_features` and `optional_features` is the empty array `[]`.
*   Any database containing unknown features (whether required or optional) MUST trigger an explicit `InvalidStorageFormat` rejection. (Read-only fallbacks for optional features are explicitly out of scope for V1).

## 15. Migration Policy
In the post-V1 stable era, any change to the storage format requires an explicit migration pathway.

*   **V1 Migration Tracking**: For V1, migration tracking is managed purely through `schema_version` in the metadata table and `PRAGMA user_version` in the SQLite file.
*   **Future Enhancements**: A dedicated `storage_migration_tbl` for tracking complex migration history is reserved as a future enhancement.
*   Implementations must provide deterministic migration routines to upgrade schemas, re-wrap keys, or alter metadata layouts.
*   Downgrades are not generally supported, and newer library versions operating on older formats may require one-way migrations.

## 16. Conformance Requirements
Before declaring V1 stable, implementations of this storage format MUST pass a comprehensive suite of cross-language test vectors to guarantee interoperability:

*   JCS Canonicalization Vectors
*   AAD Reconstruction Vectors
*   Argon2id KDF Vectors
*   AES-256-GCM AEAD Primitive Vectors
*   Key-Wrap Operation Vectors
*   Payload Encryption Vectors
*   Semantic Interoperability (Roundtrip) Tests across SQLite profiles (Python ↔ Node.js).
*   **V1 Metadata/Version Tests**: Automated tests proving metadata writing/reading, and strict rejection of unknown formats and unknown required/optional features.

*Note: While Go and Rust implementations are planned to prove broader portability, they are NOT strictly required to declare the Python, Node.js, and browser-test implementations of V1 stable.*

## 17. V1 Stabilization Criteria
The following criteria must be met before transitioning this document from Draft to Stable:

1.  `storage-format.md` and `storage-format-sqlite.md` are updated from Draft to Stable.
2.  `schema.sql` contains V1 metadata/versioning structures and required SQLite constraints.
3.  Python, Node.js, and browser-test implementations can initialize and open V1 databases.
4.  Python ↔ Node.js roundtrip integration tests pass.
5.  All shared test vectors (JCS, AAD, KDF, AEAD, Key-Wrap, Payload) pass.
6.  Unknown `format_major` values are properly rejected.
7.  Any unknown feature (required or optional) is properly rejected.
8.  `provider_config_json` explicitly includes `kdf`, `profile`, `output_bytes`, etc., and passes strict validation against the V1 profile parameters.
9.  No `aad_context_json` is stored anywhere in the schema.
10. `implementation-gaps.md` has exactly zero remaining "v1-blocking storage-format gaps".

## 18. Known Draft Gaps (V1-Blocking vs. Future Hardening)
The following issues track the difference between the decisions written above and current implementation state:

**V1-Blocking Implementation Gaps:**
None. All V1-blocking gaps have been resolved.




**Future Hardening (Post-V1):**
1.  **Schema Fingerprint / Hash**: Calculating and verifying a canonical SQL `schema_hash` to guarantee exact DDL integrity is deferred.
2.  **Optional Feature Fallback**: Implementing a strictly read-only mode for unknown optional features is deferred. V1 strictly rejects them.
3.  **Migration Tracking Table**: A dedicated `storage_migration_tbl` is deferred.
4.  **Safe Integer Policy**: A strict numeric portability policy across languages for JSON payloads is deferred.
