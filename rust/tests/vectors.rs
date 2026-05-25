use serde::Deserialize;
use std::fs;
use vault_moukaeritai_work::{test_vector_path, test_vectors_dir};

#[derive(Debug, Deserialize)]
struct AADPolicyTestCase {
    name: String,
    policy: String,
    description: String,
    expected_hex: String,
}

#[test]
fn test_vectors_dir_exists() {
    let dir = test_vectors_dir().expect("Test vectors directory must exist");
    println!("Found test vectors directory at: {:?}", dir);
}

#[test]
fn test_load_aad_vectors() {
    let path = test_vector_path("aad/aad-policies-v1.json")
        .expect("Failed to locate AAD vector file");

    let content = fs::read_to_string(&path)
        .expect("Failed to read AAD vector file");

    let vectors: Vec<AADPolicyTestCase> = serde_json::from_str(&content)
        .expect("Failed to parse AAD JSON array");

    assert!(!vectors.is_empty(), "Loaded AAD vectors but found no test cases");
    println!("Successfully parsed {} AAD test vectors", vectors.len());

    for (i, tc) in vectors.iter().enumerate() {
        assert!(!tc.name.is_empty(), "Test case {} is missing a name", i);
        assert!(!tc.policy.is_empty(), "Test case {} is missing a policy", i);
        assert!(!tc.expected_hex.is_empty(), "Test case {} is missing expected hex", i);
    }
}
