use aes_gcm::{
    aead::{Aead, KeyInit},
    Aes256Gcm, Key, Nonce,
};
use serde::Deserialize;
use vault_moukaeritai_work::{aad::build_wrap_key_v1, vectors::test_vector_path};

#[derive(Debug, Deserialize)]
struct KeyWrapVector {
    #[allow(dead_code)]
    name: String,
    #[allow(dead_code)]
    description: String,
    aad_policy: String,
    #[allow(dead_code)]
    wrapped_key_class: String,
    wrapped_kid: String,
    wrapping_kid: String,
    wrapping_key_hex: String,
    wrapped_key_plaintext_hex: String,
    nonce_hex: String,
    expected_aad_hex: Option<String>,
    expected_wrapped_key_ciphertext_hex: Option<String>,
    expected_wrapped_key_tag_hex: Option<String>,
    expected_wrapped_key_ciphertext_and_tag_hex: Option<String>,
    valid: bool,
    algorithm: Option<String>, // Assuming missing means A256GCM
}

fn decode_hex(s: &str) -> Vec<u8> {
    hex::decode(s).unwrap_or_else(|e| panic!("Failed to decode hex '{}': {}", s, e))
}

#[test]
fn test_key_wrap_conformance() {
    let path = test_vector_path("key-wrap/key-wrap-v1.json")
        .expect("Failed to locate key-wrap vector file");
    let content = std::fs::read_to_string(&path).expect("Failed to read key-wrap vector file");
    let vectors: Vec<KeyWrapVector> =
        serde_json::from_str(&content).expect("Failed to parse key-wrap JSON array");

    for tc in vectors {
        let alg = tc.algorithm.as_deref().unwrap_or("A256GCM");
        if alg != "A256GCM" {
            if tc.valid {
                panic!("Unsupported algorithm '{}' in positive test vector", alg);
            }
            continue;
        }

        let wrapping_key_bytes = decode_hex(&tc.wrapping_key_hex);
        assert_eq!(
            wrapping_key_bytes.len(),
            32,
            "Expected wrapping key length 32, got {}",
            wrapping_key_bytes.len()
        );
        let wrapping_key = Key::<Aes256Gcm>::from_slice(&wrapping_key_bytes);

        let plaintext = decode_hex(&tc.wrapped_key_plaintext_hex);
        assert_eq!(
            plaintext.len(),
            32,
            "Expected wrapped key plaintext length 32, got {}",
            plaintext.len()
        );

        let nonce_bytes = decode_hex(&tc.nonce_hex);
        assert_eq!(
            nonce_bytes.len(),
            12,
            "Expected nonce length 12, got {}",
            nonce_bytes.len()
        );
        let nonce = Nonce::from_slice(&nonce_bytes);

        let mut expected_ciphertext_and_tag: Option<Vec<u8>> = None;
        if let Some(cat_hex) = &tc.expected_wrapped_key_ciphertext_and_tag_hex {
            expected_ciphertext_and_tag = Some(decode_hex(cat_hex));
        }

        if let (Some(ct_hex), Some(tag_hex)) = (
            &tc.expected_wrapped_key_ciphertext_hex,
            &tc.expected_wrapped_key_tag_hex,
        ) {
            let ct = decode_hex(ct_hex);
            let tag = decode_hex(tag_hex);
            assert_eq!(tag.len(), 16, "Expected tag length 16, got {}", tag.len());

            let mut combined = ct.clone();
            combined.extend_from_slice(&tag);

            if let Some(expected_cat) = &expected_ciphertext_and_tag {
                assert_eq!(
                    hex::encode(&combined),
                    hex::encode(expected_cat),
                    "Separated ciphertext+tag do not match concatenated ciphertext_and_tag"
                );
            } else {
                expected_ciphertext_and_tag = Some(combined);
            }
        }

        let aad_bytes = match build_wrap_key_v1(&tc.aad_policy, &tc.wrapped_kid, &tc.wrapping_kid) {
            Ok(bytes) => bytes,
            Err(e) => {
                if tc.valid {
                    panic!("AAD builder failed: {:?}", e);
                }
                continue;
            }
        };

        if let Some(expected_aad_hex) = &tc.expected_aad_hex {
            assert_eq!(
                hex::encode(&aad_bytes),
                *expected_aad_hex,
                "Reconstructed AAD does not match expected"
            );
        }

        let cipher = Aes256Gcm::new(wrapping_key);

        let payload = aes_gcm::aead::Payload {
            msg: &plaintext,
            aad: &aad_bytes,
        };

        // aes-gcm crate's encrypt appends the tag to the ciphertext, resulting in "ciphertext || tag"
        let sealed = match cipher.encrypt(nonce, payload) {
            Ok(s) => s,
            Err(e) => {
                if tc.valid {
                    panic!("Encryption failed: {}", e);
                }
                continue; // if invalid, encrypt could theoretically fail (though rare), but we mostly check decrypt
            }
        };

        if tc.valid {
            if let Some(expected_cat) = &expected_ciphertext_and_tag {
                assert_eq!(
                    hex::encode(&sealed),
                    hex::encode(expected_cat),
                    "Sealed output does not match expected"
                );
            }

            let decrypt_payload = aes_gcm::aead::Payload {
                msg: expected_ciphertext_and_tag
                    .as_deref()
                    .unwrap_or_else(|| &sealed),
                aad: &aad_bytes,
            };

            let opened = cipher.decrypt(nonce, decrypt_payload).expect("Failed to decrypt valid key-wrap");
            assert_eq!(
                hex::encode(&opened),
                hex::encode(&plaintext),
                "Opened plaintext does not match expected"
            );
        } else {
            if let Some(expected_cat) = &expected_ciphertext_and_tag {
                let decrypt_payload = aes_gcm::aead::Payload {
                    msg: expected_cat,
                    aad: &aad_bytes,
                };
                if cipher.decrypt(nonce, decrypt_payload).is_ok() {
                    panic!("Expected failure to open negative key-wrap, but it succeeded");
                }
            }
        }
    }
}
