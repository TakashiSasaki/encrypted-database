use hex;
use serde::Deserialize;
use argon2::{Algorithm, Argon2, Params, Version};

use vault_moukaeritai_work::vectors;
use vault_moukaeritai_work::base64url;

#[derive(Deserialize)]
struct Argon2idParameters {
    memory_kib: u32,
    iterations: u32,
    parallelism: u32,
    salt_bytes: usize,
    output_bytes: usize,
}

#[derive(Deserialize)]
struct Argon2idInput {
    passphrase: String,
    salt_hex: Option<String>,
    salt: Option<String>,
}

#[derive(Deserialize)]
struct Argon2idTestCase {
    profile: String,
    // description: String,
    parameters: Argon2idParameters,
    input: Argon2idInput,
    expected_output_hex: String,
}

#[test]
fn test_argon2id_kdf_vectors() {
    let vector_path = vectors::test_vector_path("kdf/argon2id-v1.json").unwrap();
    let data = std::fs::read_to_string(vector_path).unwrap();
    let cases: Vec<Argon2idTestCase> = serde_json::from_str(&data).unwrap();

    for (i, tc) in cases.iter().enumerate() {
        assert_eq!(tc.profile, "argon2id-profile-v1", "Unsupported profile in test case {}", i);

        // Validate and resolve salt
        let has_hex = tc.input.salt_hex.is_some();
        let has_b64 = tc.input.salt.is_some();

        assert!(!(has_hex && has_b64), "Test case {}: ambiguous input, both salt_hex and salt present", i);
        assert!(has_hex || has_b64, "Test case {}: missing salt", i);

        let salt_bytes = if let Some(ref hex_str) = tc.input.salt_hex {
            hex::decode(hex_str).expect("Failed to decode salt_hex")
        } else if let Some(ref b64_str) = tc.input.salt {
            base64url::decode_strict(b64_str).expect("Failed to decode strict base64url salt")
        } else {
            unreachable!()
        };

        assert_eq!(salt_bytes.len(), tc.parameters.salt_bytes, "Decoded salt length does not match expected length in test case {}", i);

        // Map params:
        // argon2::Params::new takes (m_cost, t_cost, p_cost, output_len)
        // memory_kib -> m_cost (in KiB)
        // iterations -> t_cost
        // parallelism -> p_cost
        // output_bytes -> output_len
        let m_cost = tc.parameters.memory_kib;
        let t_cost = tc.parameters.iterations;
        let p_cost = tc.parameters.parallelism;
        let output_len = tc.parameters.output_bytes;

        let params = Params::new(m_cost, t_cost, p_cost, Some(output_len))
            .expect("Invalid Argon2 parameters");

        let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);

        let mut derived_key = vec![0u8; output_len];
        argon2.hash_password_into(tc.input.passphrase.as_bytes(), &salt_bytes, &mut derived_key)
            .expect("Argon2 hashing failed");

        assert_eq!(derived_key.len(), output_len, "Derived key length does not match expected length in test case {}", i);

        let derived_hex = hex::encode(derived_key);
        assert_eq!(derived_hex, tc.expected_output_hex, "Derived key does not match expected output in test case {}", i);
    }
}
