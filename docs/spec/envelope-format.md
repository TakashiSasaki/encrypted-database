# Envelope Format

To ensure future algorithm agility, backward compatibility, and proper metadata binding, all encrypted items (both payloads and wrapped keys) must be versioned envelopes.

Both external JSON envelopes and SQLite internal representations must include an envelope format version (`envelope_v`) and an envelope type (`envelope_type`).

## Standard JSON Envelope (v1)

For encrypted payloads, the standard version-1 JSON envelope is:

```json
{
  "v": 1,
  "type": "aead",
  "alg": "A256GCM",
  "kid": "550e8400-e29b-41d4-a716-446655440000",
  "nonce": "base64url-no-padding",
  "ct": "base64url-no-padding",
  "aad_policy": "record-payload-v1"
}
```

| Field | Description |
|---|---|
| `v` | Envelope format version (always integer). |
| `type` | Envelope type (e.g., `aead` for encrypted payloads). |
| `alg` | The encryption algorithm (e.g., `A256GCM`). |
| `kid` | The UUIDv4 of the key used to encrypt the payload. |
| `nonce` | AEAD nonce (96-bit for AES-GCM), encoded as base64url without padding. |
| `ct` | Ciphertext, including the authentication tag for AES-GCM, encoded as base64url without padding. |
| `aad_policy` | The name of the rule used to generate the AAD. |

## SQLite Representation

Within the SQLite database, envelopes are decomposed into columns. See the SQLite documentation for details on how `envelope_v` and `envelope_type` are implemented.

## Nonce and IV Generation

Nonces MUST be strictly randomly generated for each encryption operation. Never reuse a nonce for the same key. The recommended length is 96 bits (12 bytes) for AES-GCM.
