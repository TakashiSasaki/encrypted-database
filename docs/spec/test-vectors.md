# Test Vectors and Portability

To guarantee interoperability between different language implementations (e.g., Python, Node.js, WebAssembly browsers) and future migration pathways, implementations must verify their cryptographic operations and canonicalizations against standard test vectors.

## JSON Canonicalization (JCS) Vectors

Implementations must ensure their JSON serialization exactly matches the bytes produced by an RFC 8785 compliant parser. The canonicalization boundaries in both Python and Node.js implementations are backed by RFC 8785 JCS compliant libraries and verified against shared cross-language test vectors.

Any JSON values whose bytes are authenticated, hashed, MACed, signed, indexed, or used as UUID/hash input, or compared across test suites, must be strictly canonicalized.

## AAD Test Vectors

Shared machine-readable test vectors are available in `test-vectors/aad/aad-policies-v1.json`.

Implementations must verify their AAD byte generation logic using provided test vectors. The requirements for AAD test vectors include:
- AAD policy name.
- AAD context object.
- Expected JCS canonical JSON string.
- Expected AAD bytes, preferably represented as lowercase hexadecimal.
- At least one AES-GCM test vector using:
  - fixed key
  - fixed nonce
  - fixed plaintext
  - fixed AAD bytes
  - expected ciphertext plus authentication tag

Python and Node.js implementations must verify these vectors in their CI or test suites.

## UUID Formats

UUIDv4 generation must output the standard lowercase hyphen-separated format (e.g., `550e8400-e29b-41d4-a716-446655440000`). Test suites should explicitly verify string equivalence.

## Cryptographic Output

### Key Derivation (KDF) Test Vectors

A cross-language machine-readable test vector for Argon2id is available in `test-vectors/kdf/argon2id-v1.json`. This tests the standard Profile V1 (`memory_kib=65536, iterations=3, parallelism=1, salt_bytes=16, output_bytes=32`) against a fixed passphrase and salt to ensure byte-for-byte equivalence across Python, Node.js, and browser environments.

### AEAD Test Vectors

While AES-GCM nonces are randomly generated, deterministic tests should be implemented by allowing test environments to inject fixed nonces. This allows cross-language verification that:
1. Argon2id generates identical bytes given the same passphrase, salt, and parameters.
2. AES-GCM generates the identical ciphertext and tag given the same plaintext, key, nonce, and AAD bytes.

These tests should be incorporated into CI pipelines.
