# AAD Policy

Authenticated Encryption with Associated Data (AEAD) allows binding a ciphertext to its storage context using Additional Authenticated Data (AAD). If the context changes (e.g., an encrypted payload is moved to a different record ID or different schema), decryption will fail, preventing accidental or malicious swaps.

The actual AAD byte sequence is generated deterministically within the library according to the `aad_policy`. Neither the JSON envelope nor the database stores the full AAD string; they only store the policy name.

## Generating AAD

The input dictionary is constructed based on the policy, and then serialized to JSON using the RFC 8785 JSON Canonicalization Scheme (JCS). The bytes of the resulting JSON string are passed as the AAD to the AEAD algorithm.

## Cross-language AAD byte equivalence

- AAD bytes are the UTF-8 bytes of the RFC 8785 JCS-canonicalized AAD context object.
- AAD bytes are not a hash of the plaintext.
- AAD bytes are not a hash of the metadata.
- For the same `aad_policy` and same input values, every conforming implementation MUST produce byte-for-byte identical AAD bytes.
- This requirement applies to Python, Node.js, browser/WebAssembly, and any future implementation.
- If implementations produce different AAD bytes, ciphertext portability breaks because AEAD tag verification will fail during decryption.
- AAD context objects should use stable, deterministic, low-ambiguity values such as UUIDv4 canonical strings, ASCII policy names, content types, and algorithm identifiers.
- Avoid putting arbitrary human-readable labels, locale-dependent strings, runtime-specific values, or non-normalized Unicode strings into AAD context unless their canonical byte representation is fully specified.

**Immutability of AAD-bound columns:**
Columns or values that are included in the AAD context must not be changed without re-encrypting the payload or otherwise producing a new valid ciphertext/tag pair. For `record-payload-v1`, changing `object_uuid`, `schema_uuid`, `content_type`, `kid`, `alg`, or `aad_policy` after encryption will cause decryption authentication to fail.

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

**Example:**

AAD context object:

```json
{
  "v": 1,
  "aad_policy": "record-payload-v1",
  "object_uuid": "11111111-1111-4111-8111-111111111111",
  "schema_uuid": "22222222-2222-4222-8222-222222222222",
  "content_type": "application/json",
  "kid": "33333333-3333-4333-8333-333333333333",
  "alg": "A256GCM"
}
```

Expected JCS canonical JSON string:

```json
{"aad_policy":"record-payload-v1","alg":"A256GCM","content_type":"application/json","kid":"33333333-3333-4333-8333-333333333333","object_uuid":"11111111-1111-4111-8111-111111111111","schema_uuid":"22222222-2222-4222-8222-222222222222","v":1}
```

The AAD bytes are the UTF-8 bytes of that exact canonical JSON string.

## Important Security Rules

- **Do not include secrets in AAD.** AAD is authenticated, but not encrypted. It is often fully derivable from plaintext database columns.
- **Strict Byte Equivalence:** The generated AAD must match exactly, byte-for-byte, on encryption and decryption. This makes correct JCS implementation critical.
