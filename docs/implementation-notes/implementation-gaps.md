# Implementation Gaps

This document tracks known discrepancies and gaps between the current specifications/decisions and the existing codebase or integrated draft specification. This is part of the Phase 1 documentation refactor.

## Known Gaps

*   **Main Spec Examples:** The main draft specification (`docs/encrypted_storage_key_management_spec.md`) still contains stale prefixed `kid` examples which have been superseded by the UUIDv4 decision.
*   **Main Spec `cross_platform` Discussion:** The main draft still discusses `cross_platform` despite it being explicitly prohibited by later decisions.
*   **Main Spec SQL Snippets:** Some SQL snippets within the main draft are older and out of sync with the actual schema defined in `docs/schema.sql`.
*   **JSON Canonicalizers:** The current Python and Node.js implementations use prototype JSON canonicalization, and are not yet full RFC 8785 JSON Canonicalization Scheme (JCS) implementations.
*   **Test Initializations:** Existing Python and Node.js tests may call `initializeDatabase` or `initialize_database` without specifying a required concrete platform.
*   **Missing Documentation:** The Python and Node.js implementation `README.md` files are still marked as TBD.
*   **Deferred Schema Changes:** The inclusion of `wrap_id` in `wrapped_key_tbl` remains a deferred decision, meaning the schema and code do not currently support multi-generational wrap IDs for the same logical pair.

# Specification Issues Report

During the implementation of the encrypted database library based on the current draft specification (`docs/encrypted_storage_key_management_spec.md`), the following issues and discrepancies were discovered and resolved to allow for basic implementation.

## 1. Missing Platform and Policy Configurations in Test Environments
The schema enforces strict foreign key constraints across `unlock_kek_tbl`, `platform_tbl`, and `unlock_provider_platform_tbl`. However, when initializing a database without explicit environment/platform binding (e.g. running in standard headless CI pipelines or language unittests without explicit OS bindings), the initial insert to `unlock_kek_tbl` failed because the dummy platform `cross_platform` wasn't inserted into `platform_tbl` natively, and the explicit mapping for `passphrase_argon2id` and `cross_platform` was not created in `unlock_provider_platform_tbl`.
**Resolution:** Explicitly added the `cross_platform` entries into the test schema scripts. The specification should consider adding `cross_platform` bindings as base defaults for providers like Argon2id to simplify integration test environments.

## 2. AAD Context Generation Policy Versions
The `wrapped_key_tbl` examples referenced `"aad_policy": "wrap-database-key-v1"`, and the library implicitly creates such schemas. This aligns with the spec, but it should be explicitly highlighted that each time a key-wrapping is executed, a new AAD policy representation needs to match its context exactly. The library canonicalizes JSON with specific rules (`sort_keys`, `no_spaces`) before deriving AAD bytes.

## 3. Strict UUID formats
UUID v4 generation libraries in different languages (e.g., Python's `uuid.uuid4()` vs Node's `uuidv4()`) can output strings natively, but these strings needed to be consistently formatted. The implementation used standard lowercase hyphen-separated strings. Future revisions of the specification should rigidly clarify the string representation to prevent accidental UUID byte vs string mismatch bugs across libraries.

## 4. SQLite Syntax Considerations
In Node.js, `better-sqlite3` uses PRAGMA constraints. To avoid silent failures on updates and deletes, `PRAGMA foreign_keys = ON;` must be strictly enforced upon the connection opening. This library enforces it immediately in the connection constructors.
