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