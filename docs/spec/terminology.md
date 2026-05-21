# Terminology

## Identifiers and JSON Canonicalization Policy

`kid` and other identifiers (`object_uuid`, `schema_uuid`, `wrap_id`) MUST be a UUID string (versions 1 through 8 are accepted) formatted as standard lowercase, hyphen-separated values (e.g., `550e8400-e29b-41d4-a716-446655440000`). Human-readable prefixes (like `ulk-`, `dbk-`, `dek-`), key types, provider names, or purpose names MUST NOT be embedded in the `kid`.

Key semantics MUST be stored in explicit metadata columns such as `key_class`, `purpose`, `alg`, `status`, `created_at_ms`, `unlock_provider`, `created_on_platform`, and `description_json`.

Rationale: Identifiers should remain stable across renaming, reclassification, migration, and UI changes. Encoding meaning in `kid` creates metadata leakage and makes later normalization difficult. Using standard UUID formats ensures maximum interoperability and avoids metadata leakage in the string itself.

## JSON Canonicalization

All JSON values that are persisted, authenticated, hashed, MACed, signed, indexed, or used as UUID/hash input MUST be canonicalized according to the RFC 8785 JSON Canonicalization Scheme (JCS).

This includes at least:
- `description_json`
- `provider_config_json`
- plaintext JSON payload before encryption
- blind-index input values represented as JSON
- future signature, MAC, hash, or UUID input JSON
- test vector JSON values whose bytes are compared across implementations

> **Note:** Implementations MUST NOT treat `json.dumps(..., sort_keys=True)` or a simple recursive key-sort plus `JSON.stringify()` as automatically equivalent to JCS. Those techniques may be useful implementation steps, but they are insufficient unless the complete RFC 8785 requirements are satisfied. The current Python and Node.js JSON canonicalization is prototype-only and not yet full RFC 8785 JCS unless the implementation is upgraded or a compliant library is used.

If an implementation language lacks a suitable JCS library, the implementation MUST provide its own JCS-compatible canonicalizer and test it against shared test vectors.

Rationale: AAD, HMAC, hash, UUID, and cross-language test vectors depend on byte identity, not only semantic JSON equivalence. Python and Node.js default JSON serializers can differ in Unicode escaping, number serialization, object key ordering details, and edge-case handling.

## KEK and DEK

- **KEK (Key Encryption Key):** A key used to wrap or unwrap other keys.
- **DEK (Data Encryption Key):** A key used to encrypt actual data, such as payloads or blobs.
