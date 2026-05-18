# AAD Policy

Authenticated Encryption with Associated Data (AEAD) allows binding a ciphertext to its storage context using Additional Authenticated Data (AAD). If the context changes (e.g., an encrypted payload is moved to a different record ID or different schema), decryption will fail, preventing accidental or malicious swaps.

The actual AAD byte sequence is generated deterministically within the library according to the `aad_policy`. Neither the JSON envelope nor the database stores the full AAD string; they only store the policy name.

## Generating AAD

The input dictionary is constructed based on the policy, and then serialized to JSON using the RFC 8785 JSON Canonicalization Scheme (JCS). The bytes of the resulting JSON string are passed as the AAD to the AEAD algorithm.

### Policy: `wrap-database-key-v1`

Used when wrapping a `database_kek` with an `unlock_kek`.

**Input values:**
- `v`: 1
- `aad_policy`: "wrap-database-key-v1"
- `wrapped_kid`: The UUIDv4 of the key being wrapped.
- `wrapping_kid`: The UUIDv4 of the key doing the wrapping.

### Policy: `wrap-record-key-v1`

Used when wrapping a `record_dek` or `file_dek` with a `database_kek` or `workspace_kek`.

**Input values:**
- `v`: 1
- `aad_policy`: "wrap-record-key-v1"
- `wrapped_kid`: The UUIDv4 of the key being wrapped.
- `wrapping_kid`: The UUIDv4 of the key doing the wrapping.

### Policy: `record-payload-v1`

Used when encrypting an object payload.

**Input values:**
- `v`: 1
- `aad_policy`: "record-payload-v1"
- `object_uuid`: The UUIDv4 of the record.
- `schema_uuid`: The UUIDv4 of the schema defining the record.
- `content_type`: The content type (e.g., `application/json`).
- `kid`: The UUIDv4 of the `record_dek` used to encrypt the payload.
- `alg`: The encryption algorithm (e.g., `A256GCM`).

## Important Security Rules

- **Do not include secrets in AAD.** AAD is authenticated, but not encrypted. It is often fully derivable from plaintext database columns.
- **Strict Byte Equivalence:** The generated AAD must match exactly, byte-for-byte, on encryption and decryption. This makes correct JCS implementation critical.
