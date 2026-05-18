# Open Questions and Ongoing Considerations

This document tracks unresolved design questions, ongoing considerations, and future work items extracted from the main specification draft.

## 1. Accepted Directions with Remaining Implementation Details

*   **`kid` Generation:** With `kid` accepted as UUIDv4 (ADR-0001), it remains to be decided whether the library internally generates the UUIDv4 exclusively, or if the caller is allowed to provide a pre-generated UUIDv4.
*   **UUIDv4 Validation Location:** While ADR-0001 defines the format, it is an open detail whether to enforce this canonical lowercase hyphen-separated string format strictly via SQLite `CHECK` constraints, or solely via library validation. Additionally, whether 16-byte BLOBs could be used internally within SQLite is still debated.
*   **JSON Canonicalization Compliance:** RFC 8785 JCS is accepted as the standard (ADR-0002). The remaining work involves fully implementing this standard strictly in all languages and resolving whether any legacy non-strict canonical JSON approaches (like Python's `sort_keys=True`, `separators=(",", ":")`) need backwards compatibility during migration.
*   **Normalization Timing:** Whether `description_json`, `provider_config_json`, and `aad_context_json` should be fully JCS-normalized *before* saving to the DB, or if they are just validated upon write and normalized upon reading. (Save-time normalization is recommended).
*   **Provider Config Schema Registry:** Whether the schema registry for `provider_config_json` validation should be stored inside the database, or fixed within the code.

## 2. Key Wrapping and Schema

*   **`wrap_id`:** The primary key for `wrapped_key_tbl` currently relies on `(wrapped_kid, wrapping_kid)`, which struggles with multiple generations of the same wrap. The introduction of a dedicated `wrap_id` UUIDv4 is a deferred decision that needs to be finalized.
*   **Per-wrap Status:** Whether wrap rows should have independent status (`status`, `created_at_ms`, `deactivated_at_ms`, `destroyed_at_ms`) separate from the main `key_tbl.status` to handle multiple unwrap paths.
*   **Encrypted Object Versioning:** Whether `encrypted_object_tbl` should only support overwrite updates, or keep a version history of the ciphertext for synchronization and auditing purposes.
*   **Workspace KEK:** Whether to implement `workspace_kek` in the initial phase, or delay it until sharing, project boundaries, or collection boundaries are required.
*   **Device Table:** Whether to introduce a `device_tbl` for tying OS secret stores or hardware tokens to specific devices via `unlock_kek_tbl.device_id`.
*   **Platform Granularity:** Evaluating if the current platforms (`windows`, `macos`, `linux`, `android`, `ios`, `web`, `server`, `cloud`) are sufficient, or if finer granularity like `windows_service`, `linux_headless`, or `browser_extension` is needed.
*   **Provider Policy Table:** Deciding whether to introduce an `unlock_provider_policy_tbl` to separate provider definitions from app/organization/platform allow/deny policies.

## 3. Cryptography and Algorithms

*   **Blind Index Details:** Specifications around blind indexes (e.g., HMAC) need definition. This includes deciding which fields can be blind indexed, prohibiting low-entropy values, and managing index key rotation.
*   **AAD Policy Versioning:** How to define and migrate AAD policies like `record-payload-v1`, `wrap-record-key-v1`, `wrap-database-key-v1`.
*   **Algorithm Verification:** Formalizing the implementation rules that reject operations if the envelope `alg`, `key_tbl.alg`, and `key_profile_tbl.alg` do not match.
*   **AEAD Extension:** Planning the roadmap for supporting algorithms beyond `A256GCM` (e.g., `XCHACHA20-POLY1305`) or unwrap methods native to platform key handles.
*   **Nonce Generation and Limits:** Defining rules for the standard 96-bit random nonce, including encryption limits, rotation thresholds, and prohibiting deterministic nonces in production.

## 4. Operation, Error Handling, and Security

*   **API Error Model:** Defining a standard internal categorization for errors (e.g., auth tag mismatch, key not found, provider unavailable, policy violation) while ensuring that external error messages do not leak excessive information.
*   **Event/Audit Log:** Determining whether key creation, wrap creation, provider updates, and recovery events should be recorded in a dedicated audit log.
*   **Memory Handling Limitations:** Acknowledging the limitations of memory wiping in certain languages (like Python) and establishing threat models and guidelines for scope limiting and minimizing the lifetime of secret material.
*   **Log Restrictions:** Formalizing rules forbidding the logging of plaintext keys, passwords, recovery codes, nonces, ciphertexts, or decrypted payloads. Determining the strict boundary between debug and production logs regarding metadata (like UUIDs).
*   **Key Destruction Semantics:** Clarifying what `status = 'destroyed'` entails. Is it just a logical flag, or must the underlying wrap blobs be physically erased? How is referential integrity maintained if physically deleted?
*   **Backup and Recovery Semantics:** Documenting failure scenarios (what happens if the SQLite file, OS store, Shamir shares, or KMS policy is lost) and establishing testing procedures for full recovery.
*   **Payload Encryption Granularity:** Whether to encrypt entire JSON objects as a single payload, or support field-level encryption. This impacts searchability, syncing, and metadata leakage.
*   **File/Blob Encryption:** Creating a dedicated specification for `file_dek`, including chunked encryption, streaming AEAD, and file metadata protection.
*   **Migration/Versioning:** Establishing the strategy for migrating schema versions, envelope versions, provider config schemas, and AAD policies.

## 5. Architectural Considerations

*   **Threat Model Formalization:** The exact threat model needs to be documented, specifying the level of defense against DB file theft, same-user malware, admin-level attacks, and backup leaks.
*   **Metadata Leakage Tolerance:** Reviewing the acceptability of leaking metadata such as `object_uuid`, `schema_uuid`, `content_type`, and timestamps.
*   **Sync and Replication Key Model:** Defining how `unlock_kek` is added, revoked, or synchronized across multiple devices for the same database.
*   **Atomicity of KEK Updates:** Ensuring that adding a provider or changing a password (which updates wrap rows) is a safe transaction that won't result in an unrecoverable database if interrupted.
*   **KDF Parameter Updates:** Designing a migration path for increasing Argon2id parameters (memory/iterations) by simply re-wrapping the `database_kek`.
*   **OS Store Fallbacks:** Ensuring UI and processes guarantee a fallback (like a passphrase or recovery route) when an OS secret store (e.g., DPAPI/Keychain) is lost.
*   **Hardware Token Handling:** Incorporating mechanisms to handle hardware token features like PIN, touch requirements, and rate limits/lockouts into `provider_config` and error handling.
*   **KMS Dependencies:** Accounting for offline unavailability, revocation, region failures, and API limits when using remote KMS providers.
*   **Ciphertext Portability:** Defining how strictly canonical JSON, base64url, and date formats must be enforced to ensure cross-language decryption compatibility.
*   **Failure UX:** Designing user experiences for distinguishing between incorrect passwords, failed OS unlocks, missing hardware tokens, and insufficient Shamir shares.
*   **Verification Test Vectors:** Generating fixed test vectors for keys, nonces, AAD, and ciphertexts to verify cross-implementation compatibility.
*   **Security Review Boundary:** Explicitly defining the library's security scope (envelopes, key hierarchy, DB constraints) versus delegating raw crypto primitives to established underlying libraries.