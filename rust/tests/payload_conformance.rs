use serde::Deserialize;
use serde_json::Value;

use vault_moukaeritai_work::aad::build_record_payload_v1;
use vault_moukaeritai_work::jcs::canonicalize;
use vault_moukaeritai_work::vectors::test_vector_path;

use aes_gcm::{
    Aes256Gcm, Nonce,
    aead::{Aead, KeyInit, Payload},
};

#[derive(Debug, Deserialize)]
struct PayloadVector {
    name: String,
    valid: bool,
    object_uuid: Option<String>,
    schema_uuid: Option<String>,
    content_type: Option<String>,
    kid: Option<String>,
    alg: Option<String>,
    record_dek_hex: Option<String>,
    nonce_hex: Option<String>,
    payload_json: Option<Value>,
    expected_payload_jcs_hex: Option<String>,
    expected_aad_hex: Option<String>,
    expected_ciphertext_hex: Option<String>,
    expected_tag_hex: Option<String>,
    expected_ciphertext_and_tag_hex: Option<String>,
}

#[test]
fn test_payload_conformance() {
    let path = test_vector_path("payload/payload-encryption-v1.json")
        .expect("Failed to locate payload vector file");
    let content = std::fs::read_to_string(path).expect("Failed to read payload vector file");
    let vecs: Vec<PayloadVector> =
        serde_json::from_str(&content).expect("Failed to parse vector JSON");

    for vec in vecs {
        let valid = vec.valid;
        let name = &vec.name;

        let alg = match &vec.alg {
            Some(a) => a.as_str(),
            None => {
                if valid {
                    panic!("test '{}': missing alg", name);
                }
                continue;
            }
        };

        if alg != "A256GCM" {
            if valid {
                panic!(
                    "test '{}': unsupported algorithm {} in positive test",
                    name, alg
                );
            } else {
                continue;
            }
        }

        let key_hex = match &vec.record_dek_hex {
            Some(h) => h.as_str(),
            None => {
                if valid {
                    panic!("test '{}': missing record_dek_hex", name);
                }
                continue;
            }
        };

        let key = match hex::decode(key_hex) {
            Ok(k) => k,
            Err(_) => {
                if valid {
                    panic!("test '{}': invalid key hex", name);
                }
                continue;
            }
        };

        if key.len() != 32 {
            if valid {
                panic!("test '{}': invalid key length", name);
            }
            continue;
        }

        let nonce_hex = match &vec.nonce_hex {
            Some(h) => h.as_str(),
            None => {
                if valid {
                    panic!("test '{}': missing nonce_hex", name);
                }
                continue;
            }
        };

        let nonce = match hex::decode(nonce_hex) {
            Ok(n) => n,
            Err(_) => {
                if valid {
                    panic!("test '{}': invalid nonce hex", name);
                }
                continue;
            }
        };

        if nonce.len() != 12 {
            if valid {
                panic!("test '{}': invalid nonce length", name);
            }
            continue;
        }

        if let Some(tag_hex) = &vec.expected_tag_hex {
            let tag = match hex::decode(tag_hex) {
                Ok(t) => t,
                Err(_) => {
                    if valid {
                        panic!("test '{}': invalid expected_tag_hex", name);
                    }
                    continue;
                }
            };
            if tag.len() != 16 {
                if valid {
                    panic!("test '{}': invalid tag length", name);
                }
                continue;
            }
        }

        if vec.object_uuid.is_none()
            || vec.schema_uuid.is_none()
            || vec.content_type.is_none()
            || vec.kid.is_none()
        {
            if valid {
                panic!("test '{}': missing AAD reconstruction fields", name);
            }
            continue;
        }

        let reconstructed_aad = match build_record_payload_v1(
            vec.object_uuid.as_deref().unwrap(),
            vec.schema_uuid.as_deref().unwrap(),
            vec.content_type.as_deref().unwrap(),
            vec.kid.as_deref().unwrap(),
            alg,
        ) {
            Ok(a) => a,
            Err(_) => {
                if valid {
                    panic!("test '{}': failed to reconstruct AAD", name);
                }
                continue;
            }
        };

        if let Some(expected_aad_hex) = &vec.expected_aad_hex {
            let expected_aad = match hex::decode(expected_aad_hex) {
                Ok(a) => a,
                Err(_) => {
                    if valid {
                        panic!("test '{}': invalid expected_aad_hex", name);
                    }
                    continue;
                }
            };
            if valid {
                assert_eq!(
                    reconstructed_aad, expected_aad,
                    "test '{}': reconstructed AAD does not match expected_aad_hex",
                    name
                );
            } else {
                if name.contains("invalid-aad") {
                    assert_ne!(
                        reconstructed_aad, expected_aad,
                        "test '{}': expected reconstructed AAD to differ from expected_aad_hex for AAD tampering test",
                        name
                    );
                }
            }
        }

        let payload_json = match &vec.payload_json {
            Some(p) => p,
            None => {
                if valid {
                    panic!("test '{}': missing payload_json", name);
                }
                continue;
            }
        };

        let canonical_payload_str = match canonicalize(payload_json) {
            Ok(s) => s,
            Err(_) => {
                if valid {
                    panic!("test '{}': failed to canonicalize", name);
                }
                continue;
            }
        };
        let canonical_payload = canonical_payload_str.into_bytes();

        if let Some(expected_payload_jcs_hex) = &vec.expected_payload_jcs_hex {
            let expected_payload_jcs = match hex::decode(expected_payload_jcs_hex) {
                Ok(h) => h,
                Err(_) => {
                    if valid {
                        panic!("test '{}': invalid expected_payload_jcs_hex", name);
                    }
                    continue;
                }
            };
            if valid {
                assert_eq!(
                    canonical_payload, expected_payload_jcs,
                    "test '{}': canonical payload does not match expected_payload_jcs_hex",
                    name
                );
            }
        }

        let cipher = Aes256Gcm::new_from_slice(&key).unwrap();
        let nonce_arr = Nonce::from_slice(&nonce);

        let mut expected_ciphertext_and_tag = Vec::new();
        let has_expected_ct = if let Some(ct_hex) = &vec.expected_ciphertext_and_tag_hex {
            expected_ciphertext_and_tag = match hex::decode(ct_hex) {
                Ok(c) => c,
                Err(_) => {
                    if valid {
                        panic!("test '{}': invalid expected_ciphertext_and_tag_hex", name);
                    }
                    continue;
                }
            };
            true
        } else {
            false
        };

        if valid {
            let encrypted = cipher
                .encrypt(
                    nonce_arr,
                    Payload {
                        msg: &canonical_payload,
                        aad: &reconstructed_aad,
                    },
                )
                .expect("encryption failed");

            if has_expected_ct {
                assert_eq!(
                    encrypted, expected_ciphertext_and_tag,
                    "test '{}': encrypted payload does not match expected_ciphertext_and_tag_hex",
                    name
                );
            }

            let decrypted = cipher
                .decrypt(
                    nonce_arr,
                    Payload {
                        msg: &expected_ciphertext_and_tag,
                        aad: &reconstructed_aad,
                    },
                )
                .expect("decryption failed");

            assert_eq!(
                decrypted, canonical_payload,
                "test '{}': decrypted payload does not match original canonical payload",
                name
            );
        } else {
            if has_expected_ct {
                let decrypt_result = cipher.decrypt(
                    nonce_arr,
                    Payload {
                        msg: &expected_ciphertext_and_tag,
                        aad: &reconstructed_aad,
                    },
                );
                assert!(
                    decrypt_result.is_err(),
                    "test '{}': decryption succeeded on invalid vector, expected failure",
                    name
                );
            }
        }
    }
}
