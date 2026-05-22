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

## 2. Format Stability Model
Before the V1 stabilization is officially declared, this format is considered **experimental (pre-v1)**. Destructive schema changes, backwards-incompatible cryptographic modifications, and structural alterations are permitted without migration pathways.

After V1 stabilization, the format guarantees backward compatibility. Any structural or cryptographic changes must conform to the Versioning and Compatibility Policy and Migration Policy defined below.

## 3. Storage Format Identity
A storage file must contain metadata to identify its format, version, and origin. This ensures that implementations can correctly identify and read the structure.

Candidate components for Storage Format Identity include:
*   **`storage_format_id`**: A fixed string or magic number identifying the database format.
*   **`format_major`**: Major version number (e.g., 1). Changes indicate breaking changes requiring migration.
*   **`format_minor`**: Minor version number (e.g., 0). Changes indicate backward-compatible additions.
*   **`schema_version`**: A version or hash tracking the specific underlying schema layout (e.g., SQLite DDL version).
*   **`database_uuid`**: A canonical UUID uniquely identifying this specific database instance.
*   **`created_at_ms`**: Unix timestamp in milliseconds indicating when the database was created.
*   **`created_by_library`**: A string indicating the library implementation that created the database (e.g., `"python-vault"`, `"nodejs-vault"`). Note that the library version and storage format version are fundamentally separate.
*   **`created_by_version`**: The version string of the library that created the database.
*   **`required_features`**: A list of feature flags that a reader MUST understand to open the database.
*   **`optional_features`**: A list of feature flags that a reader MAY understand to utilize enhancements.
*   **`schema_hash` / Schema Fingerprint**: A proposed candidate to assert the exact underlying database schema integrity. (Not yet implemented, see Draft Gaps).

## 4. Versioning and Compatibility Policy
This policy outlines how implementations handle versioning and feature flags (Draft Candidates for V1):

*   **Format Major Mismatch**: If the `format_major` of the database is greater than the implementation's supported major version, the implementation MUST reject opening the database.
*   **Format Minor Mismatch**: If the `format_minor` of the database is greater than the implementation's supported minor version, the implementation MAY attempt to open it, provided no unknown `required_features` are present.
*   **Unknown Required Features**: If the database requires a feature flag not implemented by the reader, the implementation MUST reject opening the database to prevent data corruption or security downgrade.
*   **Unknown Optional Features**: If the database contains unknown optional features but no unknown required features, the implementation MAY open the database. (Potential V1 Policy: Fallback to a strictly read-only mode to prevent overwriting or deleting data reliant on optional features).
*   **Destructive Changes**: V1 stabilization prohibits destructive changes without an explicit migration policy. In the pre-v1 state, destructive changes are fully permitted.

## 5. Database Identity and Metadata
Every initialized database possesses a single identity encompassing the identity components described in Section 3. The precise mechanism for storing this identity (e.g., a metadata table) is deferred to the physical storage profile.

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
*   **Argon2id Profile V1**: The current implementation strictly uses the `passphrase_argon2id` provider with Profile V1 values for database initialization:
    *   `memory_kib` = 65536
    *   `iterations` = 3
    *   `parallelism` = 1
    *   `salt_bytes` = 16
    *   `output_bytes` = 32
*   These configuration values are read dynamically during the unlock process.
*   *Draft Gap*: Whether strictly invariant values like `kdf`, `profile`, and `output_bytes` should be explicitly embedded within the JSON config or implicitly defined by the provider ID remains a topic for V1 hardening.

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
The storage format relies on strict JSON Canonicalization Scheme (RFC 8785).

*   **Payload Encryption**: The plaintext input to the payload encryption cipher MUST be the JCS-canonicalized bytes of the payload JSON.
*   **Provider Config**: The `provider_config_json` stored in the database MUST be JCS-canonicalized.
*   **AAD Context**: The AAD bytes input to the AES-GCM cipher MUST be the JCS-canonicalized bytes of the reconstructed AAD context object.
*   **No Native Serializers**: Implementations MUST NOT use standard language-native JSON serializers (e.g., `json.dumps()`, `JSON.stringify()`) for these cryptographic boundaries, as they do not guarantee RFC 8785 compliance.
*   **Conformance**: Python, Node.js, Web Browser, Go, and Rust implementations MUST pass shared JCS test vectors. Any value that cannot be strictly JCS-canonicalized MUST be rejected by the implementation and cannot be stored.

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
To support future extensibility without breaking format compatibility, the storage format proposes the use of required and optional feature flags.

*   **Required Features**: Features that alter cryptographic layouts, fundamentally change database semantics, or dictate necessary migration logic.
*   **Optional Features**: Performance optimizations (e.g., blind indexes) or non-critical metadata that older readers can safely ignore or preserve.
*   **Handling**: See Versioning and Compatibility Policy.

## 15. Migration Policy
In the post-V1 stable era, any change to the storage format requires an explicit migration pathway.

*   Implementations must provide deterministic migration routines to upgrade schemas, re-wrap keys, or alter metadata layouts.
*   Downgrades are not generally supported, and newer library versions operating on older formats may require one-way migrations.

## 16. Conformance Requirements
Implementations of this storage format MUST pass a comprehensive suite of cross-language test vectors to guarantee interoperability:

*   JCS Canonicalization Vectors
*   AAD Reconstruction Vectors
*   Argon2id KDF Vectors
*   AES-256-GCM AEAD Primitive Vectors
*   Key-Wrap Operation Vectors
*   Payload Encryption Vectors
*   Semantic Interoperability (Roundtrip) Tests across SQLite profiles.

## 17. Known Draft Gaps
The following issues are known gaps in the current V1 Draft proposal:

1.  **Format Identity Implementation**: `format_major`, `format_minor`, `required_features`, `optional_features` and a `metadata_tbl` are proposed but not currently implemented in the database schema or code.
2.  **Schema Fingerprint**: The mechanism for calculating and verifying a `schema_hash` or schema fingerprint is not yet defined.
3.  **Optional Feature Fallback**: The policy of allowing strictly read-only access for unknown optional features is not yet finalized.
4.  **Provider Config Explicitness**: Whether invariant Argon2id parameters (e.g., `output_bytes`) should be explicitly serialized in `provider_config_json` or remain implicit to the `passphrase_argon2id` provider definition is undecided.
5.  **Safe Integer Policy**: A strict numeric portability policy across languages (Python vs JavaScript vs Go/Rust) for payloads is not yet defined.
