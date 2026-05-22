# Storage Format V1 SQLite Profile (Draft)

```text
Status: Draft
Compatibility: pre-v1 SQLite storage profile
Implementation status: Python partial, Node.js partial, browser-test partial, Go planned, Rust planned
Normative status: Proposed SQLite profile for storage-format-v1
```

## 1. Purpose and Scope
This document specifies the SQLite physical storage profile for the Encrypted Database Storage Format V1. It defines how the abstract cryptographic invariants, metadata, and key hierarchies defined in the Storage Format Core are mapped to SQLite tables, columns, constraints, and PRAGMAs.

## 2. Relationship to Storage Format Core
This document is a physical realization of the abstract `storage-format.md`. To maintain a clean separation of concerns, the boundaries are strictly defined:

*   **Storage Format Core**: Defines UUID canonical format, key hierarchy, AEAD layout, JCS normalization, AAD reconstruction rules, provider config semantics, payload value models, and feature/versioning policies.
*   **SQLite Storage Profile**: Defines the physical tables, columns, column types, CHECK constraints, PRAGMAs, `json_valid` usage, foreign keys, transaction behavior, and the canonical `schema.sql`.

While the core defines that encrypted keys use A256GCM with a 12-byte nonce, this profile defines that those bytes are stored in specific SQLite `BLOB` columns (`nonce`, `wrapped_key`, `ciphertext`). Where SQLite provides native mechanisms (e.g., `CHECK`, `NOT NULL`, `FOREIGN KEY`), this profile leverages them. Where SQLite cannot fully enforce the invariant (e.g., recursive JSON structure validation, JCS canonicalization), this profile specifies that enforcement is deferred to the library application code.

## 3. SQLite File Identity
An SQLite database file implementing this profile should be identifiable both externally (e.g., via magic numbers) and internally.
*   **Magic Number**: Standard SQLite 3 magic header.
*   **`PRAGMA application_id`**: Used as a magic number to identify the specific file type (e.g., a specific 32-bit integer `1447906135` / `0x564D4B57` representing this vault format).
*   **`PRAGMA user_version`**: Used as an auxiliary integer tracking the SQLite schema / migration version (synchronizes with `schema_version` in the metadata table).

## 4. Required PRAGMAs
To ensure security, data integrity, and cross-platform compatibility, implementations interacting with the SQLite profile MUST execute specific PRAGMAs upon connection:
*   `PRAGMA foreign_keys = ON;` (Mandatory: Validates relationships like `wrapped_kid` referencing `kid`. Implementations must execute this immediately upon connection, and verify it is enabled if possible).
*   `PRAGMA journal_mode = WAL;` (Optional / Recommended: For concurrency and crash resilience on desktop/server, though environments like `sql.js` in the browser or in-memory backends may differ).
*   *Future Hardening*: SQLite `STRICT` tables are deferred to future enhancements due to compatibility constraints across Go/Rust drivers and older SQLite versions.

## 5. Canonical Schema Source
The definitive, unversioned schema for the current pre-v1 state is located at `docs/backend/sqlite/schema.sql`.

*Future Hardening*: A "Schema Fingerprint" derived from canonical DDL statements to verify exact database schema layout is deferred.

## 6. Table Mapping
The abstract entities from the Storage Format Core map to the following SQLite tables:

*   **`key_class_tbl`**: Enumerates valid key roles (`unlock_kek`, `database_kek`, etc.).
*   **`key_profile_tbl`**: Defines allowed cryptographic algorithms for specific key purposes.
*   **`key_tbl`**: Tracks the metadata, status, and lifecycle timestamps for every key entity (`kid`). Contains NO cryptographic material.
*   **`wrapped_key_tbl`**: Stores the AES-GCM encrypted key material (the "envelope") where a `wrapping_kid` protects a `wrapped_kid`.
*   **`encrypted_object_tbl`**: Stores the AES-GCM encrypted application payloads (records).
*   **`unlock_method_tbl` & `unlock_provider_tbl`**: Taxonomies of how `unlock_kek`s are derived or retrieved.
*   **`platform_tbl` & `unlock_provider_platform_tbl`**: Taxonomies of platform-specific provider support.
*   **`unlock_kek_tbl`**: Stores the provider configuration JSON and platform creation metadata for `unlock_kek`s.

## 7. Column Mapping and Type Rules
SQLite's dynamic typing necessitates strict rules for how data is bound and stored:

*   **UUIDs (`TEXT`)**: Must be stored as canonical, lowercase, hyphenated strings.
*   **Timestamps (`INTEGER`)**: Must be stored as Unix epoch milliseconds.
*   **Cryptographic Material (`BLOB`)**: Nonces, tags, and ciphertexts must be strictly stored as BLOBs, not base64/hex strings.
*   **Booleans (`INTEGER`)**: SQLite handles booleans as integers (`0` or `1`).

## 8. Constraints and Invariants
This profile strictly divides the enforcement of rules between the SQLite engine and the application layer.

### 8.1 SQLite Enforced Constraints
The database schema actively enforces the following using `NOT NULL`, `PRIMARY KEY`, `FOREIGN KEY`, and `CHECK` constraints:
*   **UUID Formatting**: All `UUID` columns (`kid`, `wrap_id`, `object_uuid`, `schema_uuid`) use SQLite `GLOB` checks written with repeated `[0-9a-f]` character classes (rather than `{8}`-style repetition), including explicit UUID version and variant nibble constraints, to ensure canonical formatting as defined in `docs/backend/sqlite/schema.sql`. The schema permits UUID versions `[1-8]`.
*   **Key Relationships**: `FOREIGN KEY` constraints ensure a `wrapped_key_tbl` cannot reference non-existent keys. Foreign key enforcement is a mandatory V1 requirement.
*   **Enumerations**: `CHECK(status IN ('active', ...))` and similar constraints enforce finite state machines for keys and envelopes.
*   **Static Invariants**: `envelope_v = 1`, `envelope_type = 'key_wrap'`, etc., are locked via `CHECK` constraints.
*   **JSON Shape**: `json_valid(provider_config_json)` ensures columns designated as JSON at least parse via SQLite's JSON extension. (Note: Using `json_extract()` for field-level validation is not V1-blocking and is deferred to application-layer validation).

### 8.2 Application Layer Enforced Constraints
SQLite capabilities are insufficient to enforce the following, which MUST be validated by the library implementation:
*   **JCS Canonicalization**: SQLite `json_valid` does not enforce RFC 8785 byte equivalence. The application MUST ensure JCS canonical strings are bound.
*   **Recursive Payload Validation**: SQLite cannot deeply enforce that a payload object contains only strings/numbers/booleans/nulls and no raw binary data prior to encryption.
*   **AAD Byte Construction**: SQLite has no awareness of the dynamically constructed AAD context.

## 9. BLOB Encoding Rules
*   **`nonce`**: Stores the raw 12-byte initialization vector.
*   **`wrapped_key`**: Stores the concatenated ciphertext and authentication tag (32 bytes key + 16 bytes tag = 48 bytes total) from the key-wrapping operation.
*   **`ciphertext`**: Stores the concatenated ciphertext and authentication tag of the payload encryption operation.

## 10. JSON Column Rules
Columns suffixed with `_json` (e.g., `provider_config_json`, `description_json`):
*   Must be inserted strictly as UTF-8 encoded, JCS-canonicalized text strings.
*   Are verified by SQLite's `json_valid()` function to prevent severe malformation.

## 11. Foreign Keys and Transactions
*   All operations spanning multiple tables (e.g., generating a new `record_dek` in `key_tbl` and subsequently wrapping it in `wrapped_key_tbl`) MUST be performed within a single SQLite transaction (`BEGIN` / `COMMIT`).
*   Foreign Key checking must be enabled at the connection level to ensure the graph of keys remains structurally sound.

## 12. Metadata Table Candidates
The V1 schema introduces a dedicated `storage_metadata_tbl` to support the Storage Format Core identity model. It is designed as a strict key-value structure. The application layer handles parsing the `value` column (e.g., as strings, integers, or JCS JSON arrays).

## 13. Migration Handling
SQLite schema migrations will rely on structural changes utilizing standard SQLite DDL techniques (e.g., creating temporary tables, copying data, and renaming). In V1, migrations are tracked using `schema_version` in the metadata table and `PRAGMA user_version`. A dedicated `storage_migration_tbl` is reserved as a future enhancement.

## 14. Implementation Requirements
Any library implementing this profile MUST:
1.  Provide mechanisms to bootstrap the exact `schema.sql`.
2.  Provide database connection configurations that guarantee the required PRAGMAs.
3.  Trap raw `sqlite3.Error` (or equivalent) and map them to standard `DatabaseBackendError` or input validation errors as dictated by the API contract.
4.  Correctly close database connections in `finally` blocks to release file locks across all platforms.

## 15. Proposed V1 Schema Changes
The following are proposed constraints and structures that fulfill the V1 requirements.

*Note: These are proposed V1 structures and constraints; they are not yet applied to `docs/backend/sqlite/schema.sql`.*

**Metadata Table**:
```sql
CREATE TABLE IF NOT EXISTS storage_metadata_tbl (
    property TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

**Cryptographic & Length Invariants**:

To apply the proposed constraints, the existing tables in `schema.sql` would be modified to include the following table-level or column-level constraints:

```sql
-- To be added to: CREATE TABLE wrapped_key_tbl (...)
    -- ... existing columns ...
    -- nonce BLOB NOT NULL CHECK(length(nonce) = 12),
    -- wrapped_key BLOB NOT NULL CHECK(length(wrapped_key) >= 16),
    -- Note: Current AES-GCM output is 32-byte key + 16-byte tag = 48 bytes.
    -- However, we only enforce >= 16 bytes to avoid fixing algorithm-dependent length too rigidly in the schema.

-- To be added to: CREATE TABLE encrypted_object_tbl (...)
    -- ... existing columns ...
    -- nonce BLOB NOT NULL CHECK(length(nonce) = 12),
    -- ciphertext BLOB NOT NULL CHECK(length(ciphertext) >= 16),
    -- content_type TEXT NOT NULL CHECK(length(content_type) > 0 AND instr(content_type, '/') > 1),
```

## 16. Known SQLite Profile Gaps
A review of the current `docs/backend/sqlite/schema.sql` against the V1 draft reveals the following "decided but not implemented" gaps:

1.  **Missing Metadata/Version Table**: The schema lacks `storage_metadata_tbl` to track `format_major`, `format_minor`, `required_features`, or `optional_features`.

3.  **Missing BLOB Length Constraints**: The schema lacks the `CHECK(length(nonce) = 12)`, `CHECK(length(wrapped_key) >= 16)`, and `CHECK(length(ciphertext) >= 16)` constraints.
4.  **Missing Content Type Constraints**: `content_type` lacks the `CHECK(length(content_type) > 0 AND instr(content_type, '/') > 1)` constraint.
