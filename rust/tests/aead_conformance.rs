use aes_gcm::aead::{Aead, KeyInit, Payload};
use aes_gcm::{Aes256Gcm, Key, Nonce};
use serde::Deserialize;
use std::fs;
use vault_moukaeritai_work::vectors::test_vector_path;

#[derive(Debug, Deserialize)]
struct AeadVector {
    name: String,
    // description: String,
    alg: String,
    key_hex: String,
    nonce_hex: String,
    aad_hex: String,
    plaintext_hex: String,
    // expected_ciphertext_hex: String,
    expected_tag_hex: String,
    expected_ciphertext_and_tag_hex: String,
    valid: bool,
}

#[test]
fn test_aead_conformance() {
    let path = test_vector_path("aead/aes-256-gcm-v1.json").expect("Failed to get vector path");
    let content = fs::read_to_string(&path).expect("Failed to read AEAD vectors file");
    let vectors: Vec<AeadVector> =
        serde_json::from_str(&content).expect("Failed to parse AEAD vectors JSON");

    for vector in vectors {
        if vector.alg != "A256GCM" {
            if vector.valid {
                panic!("Unsupported algorithm in valid vector: {}", vector.alg);
            } else {
                // If the test case is explicitly marked invalid, we allow it to pass as it
                // correctly failed to process an unsupported algorithm.
                continue;
            }
        }

        let key_bytes = hex::decode(&vector.key_hex).expect("Failed to decode key_hex");
        assert_eq!(key_bytes.len(), 32, "Key must be 32 bytes for AES-256-GCM");

        let nonce_bytes = hex::decode(&vector.nonce_hex).expect("Failed to decode nonce_hex");
        assert_eq!(nonce_bytes.len(), 12, "Nonce must be 12 bytes");

        let aad_bytes = hex::decode(&vector.aad_hex).expect("Failed to decode aad_hex");
        let plaintext_bytes =
            hex::decode(&vector.plaintext_hex).expect("Failed to decode plaintext_hex");
        let expected_tag_bytes =
            hex::decode(&vector.expected_tag_hex).expect("Failed to decode expected_tag_hex");
        assert_eq!(expected_tag_bytes.len(), 16, "Tag must be 16 bytes");

        let expected_ciphertext_and_tag_bytes =
            hex::decode(&vector.expected_ciphertext_and_tag_hex)
                .expect("Failed to decode expected_ciphertext_and_tag_hex");

        let key = Key::<Aes256Gcm>::from_slice(&key_bytes);
        let nonce = Nonce::from_slice(&nonce_bytes);
        let cipher = Aes256Gcm::new(key);

        let payload = Payload {
            msg: &plaintext_bytes,
            aad: &aad_bytes,
        };

        // Note: RustCrypto's aes-gcm crate's encrypt method returns a Vec<u8> which
        // appends the authentication tag to the ciphertext ("ciphertext || tag").
        // This layout matches expected_ciphertext_and_tag_hex.
        let encrypt_result = cipher.encrypt(nonce, payload);

        if vector.valid {
            // Positive case
            let encrypted = encrypt_result.expect("Encryption failed for valid case");
            assert_eq!(
                encrypted, expected_ciphertext_and_tag_bytes,
                "Encryption mismatch for test: {}",
                vector.name
            );

            // Decrypt
            let decrypt_payload = Payload {
                msg: &expected_ciphertext_and_tag_bytes,
                aad: &aad_bytes,
            };
            let decrypted = cipher
                .decrypt(nonce, decrypt_payload)
                .expect("Decryption failed for valid case");
            assert_eq!(
                decrypted, plaintext_bytes,
                "Decrypted plaintext mismatch for test: {}",
                vector.name
            );
        } else {
            // Negative case (e.g. invalid tag, invalid AAD)
            // It might fail at encryption (unlikely) or decryption (expected)
            let decrypt_payload = Payload {
                msg: &expected_ciphertext_and_tag_bytes,
                aad: &aad_bytes,
            };
            let decrypt_result = cipher.decrypt(nonce, decrypt_payload);
            assert!(
                decrypt_result.is_err(),
                "Expected decryption to fail for invalid case: {}",
                vector.name
            );
        }
    }
}
