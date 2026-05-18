# Test Vectors and Portability

To guarantee interoperability between different language implementations (e.g., Python, Node.js, WebAssembly browsers) and future migration pathways, implementations must verify their cryptographic operations and canonicalizations against standard test vectors.

## JSON Canonicalization (JCS) Vectors

Implementations must ensure their JSON serialization exactly matches the bytes produced by an RFC 8785 compliant parser. Note that current prototype canonicalization in Python and Node.js might fail edge-case RFC 8785 tests.

Any JSON values whose bytes are authenticated, hashed, MACed, signed, indexed, or used as UUID/hash input, or compared across test suites, must be strictly canonicalized.

## UUID Formats

UUIDv4 generation must output the standard lowercase hyphen-separated format (e.g., `550e8400-e29b-41d4-a716-446655440000`). Test suites should explicitly verify string equivalence.

## Cryptographic Output

While AES-GCM nonces are randomly generated, deterministic tests should be implemented by allowing test environments to inject fixed nonces and static key derivation salts. This allows cross-language verification that:
1. Argon2id generates identical bytes given the same passphrase, salt, and parameters.
2. AES-GCM generates the identical ciphertext and tag given the same plaintext, key, nonce, and AAD bytes.

These tests should be incorporated into CI pipelines.
