# ADR 0002: Require RFC 8785 JSON Canonicalization Scheme (JCS)

## Status
Accepted

## Context
Various parts of the system handle JSON data that is persisted, authenticated, hashed, MACed, signed, indexed, or used as UUID/hash input. This includes `description_json`, `aad_context_json`, `provider_config_json`, plaintext JSON payloads, blind-index inputs, and cross-language test vectors.

Different JSON serializers across platforms and languages (like Python's `json.dumps` vs Node.js's `JSON.stringify()`) handle Unicode escaping, number serialization, and key ordering differently. These differences lead to mismatched byte sequences even when the JSON is semantically equivalent, causing failures in HMAC, AAD validation, and cross-language interoperability.

## Decision
All JSON values that require deterministic byte representations MUST be canonicalized according to the RFC 8785 JSON Canonicalization Scheme (JCS).

Implementations MUST NOT rely on simple recursive key-sorting (like Python's `json.dumps(..., sort_keys=True)`) as automatically equivalent to JCS. While these might be useful steps, they are insufficient unless all RFC 8785 requirements are met.

If an implementation language lacks a suitable JCS library, the implementation MUST provide a JCS-compatible canonicalizer and verify it against shared test vectors.

## Consequences
- Guarantees byte-identity for JSON representations across all supported platforms and languages.
- Prevents subtle bugs in cryptography (AAD/HMAC verification) caused by serialization differences.
- Requires current Python and Node.js implementations (which currently use prototype canonicalizers) to be updated to full RFC 8785 JCS compliance.

## Related Files
- `docs/spec/terminology.md`
- `docs/legacy/encrypted_storage_key_management_spec.md`
- Current Python and Node.js implementations (require updates)