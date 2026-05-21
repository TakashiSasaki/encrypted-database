# Test Vectors and Portability

To guarantee interoperability between different language implementations (e.g., Python, Node.js, WebAssembly browsers) and future migration pathways, implementations must verify their cryptographic operations and canonicalizations against standard test vectors.

These primitive-level test vectors ensure byte-for-byte equivalence across platforms, which is distinct from the semantic interoperability verified by SQLite roundtrip tests.

## JSON Canonicalization (JCS) Vectors

Implementations must ensure their JSON serialization exactly matches the bytes produced by an RFC 8785 compliant parser. The canonicalization boundaries in both Python and Node.js implementations are backed by RFC 8785 JCS compliant libraries and verified against shared cross-language test suites in `test-vectors/jcs/`.

Any JSON values whose bytes are authenticated, hashed, MACed, signed, indexed, or used as UUID/hash input, or compared across test suites, must be strictly canonicalized.

## AAD Test Vectors

Shared machine-readable test vectors are available in `test-vectors/aad/aad-policies-v1.json`.

Implementations must verify their AAD byte generation logic using provided test vectors. The requirements for AAD test vectors include:
- AAD policy name.
- AAD context object.
- Expected JCS canonical JSON string.
- Expected AAD bytes, preferably represented as lowercase hexadecimal.

Python, Node.js, and browser-test implementations must verify these vectors in their CI or test suites.

## UUID Formats

UUIDv4 generation must output the standard lowercase hyphen-separated format (e.g., `550e8400-e29b-41d4-a716-446655440000`). Test suites should explicitly verify string equivalence.

## Cryptographic Output

While AES-GCM nonces and Argon2id salts are randomly generated in production, deterministic tests are implemented by allowing test environments to inject fixed nonces and static key derivation salts. This allows strict cross-language verification.

Machine-readable JSON vectors are available for the following operations:
*   **Argon2id KDF** (`test-vectors/kdf/argon2id-v1.json`): Verifies that identical keys are derived from the same passphrase, salt, and parameters.
*   **AES-256-GCM** (`test-vectors/aead/aes-256-gcm-v1.json`): Verifies that identical ciphertexts and authentication tags are generated for the same plaintext, key, nonce, and AAD bytes.
*   **Key Wrap** (`test-vectors/key-wrap/key-wrap-v1.json`): Verifies the correct AAD assembly and AEAD wrapping of cryptographic keys.
*   **Payload Encryption** (`test-vectors/payload/payload-encryption-v1.json`): Verifies the correct sequential application of JCS canonicalization, AAD assembly, and AEAD encryption for JSON payloads.

These vectors are actively verified in the Python, Node.js, and browser-test implementations.
