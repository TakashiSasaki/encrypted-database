# Test Vectors and Portability

To guarantee interoperability between different language implementations (e.g., Python, Node.js, WebAssembly browsers, and eventually Go/Rust) and future migration pathways, implementations must verify their cryptographic operations and canonicalizations against standard test vectors.

These test vectors serve as the foundational conformance suite for the Storage Format V1 Stable invariants. Note that while Go/Rust portability validation scaffolds prove broader portability, the Python/Node.js baseline implementations are sufficient for declaring V1 stable.

## JSON Canonicalization (JCS) Vectors

Implementations must ensure their JSON serialization exactly matches the bytes produced by an RFC 8785 compliant parser. The canonicalization boundaries in both Python and Node.js implementations are backed by RFC 8785 JCS compliant libraries and verified against shared cross-language test vectors.

Any JSON values whose bytes are authenticated, hashed, MACed, signed, indexed, or used as UUID/hash input, or compared across test suites, must be strictly canonicalized.

## AAD Test Vectors

Shared machine-readable test vectors are available in `test-vectors/aad/aad-policies-v1.json`.

Implementations must verify their AAD byte generation logic using provided test vectors.

## UUID Formats

UUIDv4 generation must output the standard lowercase hyphen-separated format (e.g., `550e8400-e29b-41d4-a716-446655440000`). Test suites should explicitly verify string equivalence.

## Cryptographic Output

### Key Derivation (KDF) Test Vectors

A cross-language machine-readable test vector for Argon2id is available in `test-vectors/kdf/argon2id-v1.json`. This tests the standard Profile V1 (`memory_kib=65536, iterations=3, parallelism=1, salt_bytes=16, output_bytes=32`) against a fixed passphrase and salt to ensure byte-for-byte equivalence across Python, Node.js, and browser environments. These KDF vectors have been implemented and verified in the automated tests for Python, Node.js, and browser-test environments. The browser-test Jest environment validates the same shared vectors.

Note that the KDF test vectors do not replace the SQLite roundtrip interoperability tests. The roundtrip test asserts high-level semantic interoperability between different language implementations, while the KDF test vector is a strict byte-level primitive equivalence test.

### AEAD (AES-256-GCM) Test Vectors

A cross-language machine-readable test vector for AES-256-GCM primitive operations is available in `test-vectors/aead/aes-256-gcm-v1.json`. It tests the base encryption and decryption using fixed keys, nonces, plaintext, and AAD bytes. Implementations must ensure byte-for-byte equivalence for ciphertext and authentication tags, properly handling combined or separated tag formats according to the standard. AEAD primitive checks currently use Node.js crypto in the Jest environment. This does not fully validate a real browser WebCrypto runtime path.

### Key-Wrap Test Vectors

Machine-readable test vectors for the wrapping and unwrapping of database KEKs and record DEKs are available in `test-vectors/key-wrap/key-wrap-v1.json`. Implementations must verify that they can dynamically reconstruct the correct AAD from the policy and IDs, and correctly wrap/unwrap the key materials. The browser-test Jest environment validates the same shared vectors using Node.js crypto.

### Payload Encryption Test Vectors

Machine-readable test vectors for payload encryption are available in `test-vectors/payload/payload-encryption-v1.json`. Implementations must ensure they correctly JCS-canonicalize the JSON payload before encryption, reconstruct the required AAD, and successfully encrypt/decrypt the payload. Tests must verify that variations in JSON key order resolve to the identical canonicalized bytes and result in equivalent ciphertext given the same nonce. The browser-test Jest environment validates the same shared vectors using Node.js crypto.

### Semantic Interoperability (SQLite Roundtrip)

In addition to primitive test vectors, the high-level semantic interoperability between language implementations is validated using SQLite roundtrip integration tests (`integration-tests/roundtrip/`). These tests assert that higher-level payload operations and unlocking mechanics successfully work across platforms, whereas the JSON test vectors focus on byte-level cryptographic equivalence.

### Metadata and Version Constraints

As part of V1 conformance, automated tests must verify correct metadata writing and parsing, strict rejection of unknown `format_major` values, and strict rejection of any unknown feature (required or optional).

### Storage Format Validation Tests
In addition to the static cryptographic vectors above, the V1 Conformance Suite mandates explicit behavioral tests for metadata rejection, PRAGMA contradictions, JCS canonicality enforcement, schema `CHECK` constraints, and missing KEK states. These are implemented dynamically in the Python, Node.js, and browser test suites.

## Metadata and Version Validation Tests

Implementations must verify their database provenance, version strings, JCS exactness of metadata JSON, and strict provider configurations (including base64url padding checks) through test suites. These tests are considered part of the overarching V1 conformance suite alongside cryptographic test vectors.

## Validation Conformance Suites
Beyond the cryptographic test vectors provided in `test-vectors/`, implementations MUST implement their own conformance test suites validating that malformed inputs and format manipulations are proactively rejected by the public API layers, including:
- Metadata rejection (`InvalidStorageFormat` for missing/wrong values)
- Feature flag rejection (for unknown required/optional features)
- Provider Config parameter mismatch and padding rejection
- Cross-implementation compatibility assurance tests
