use serde::Deserialize;
use serde_json::{json, Value};
use vault_moukaeritai_work::{
    jcs::canonicalize,
    vectors::{test_vector_path},
};

#[derive(Debug, Deserialize)]
struct AADVectorInput {
    object_uuid: Option<String>,
    schema_uuid: Option<String>,
    content_type: Option<String>,
    kid: Option<String>,
    alg: Option<String>,
    wrapped_kid: Option<String>,
    wrapping_kid: Option<String>,
}

#[derive(Debug, Deserialize)]
struct AADVector {
    name: String,
    policy: String,
    #[allow(dead_code)]
    description: String,
    expected_hex: String,
    expected_string: Option<String>,
    input: AADVectorInput,
}

#[test]
fn test_aad_conformance() {
    let path = test_vector_path("aad/aad-policies-v1.json")
        .expect("Failed to locate AAD vector file");

    let content = std::fs::read_to_string(&path)
        .expect("Failed to read AAD vector file");

    let vectors: Vec<AADVector> = serde_json::from_str(&content)
        .expect("Failed to parse AAD JSON array");

    for tc in vectors {
        let mut context_map = serde_json::Map::new();
        context_map.insert("v".to_string(), json!(1));
        context_map.insert("aad_policy".to_string(), json!(&tc.policy));

        match tc.policy.as_str() {
            "record-payload-v1" => {
                let obj = tc.input.object_uuid.expect("Missing object_uuid");
                let sch = tc.input.schema_uuid.expect("Missing schema_uuid");
                let ctype = tc.input.content_type.expect("Missing content_type");
                let kid = tc.input.kid.expect("Missing kid");
                let alg = tc.input.alg.expect("Missing alg");

                context_map.insert("object_uuid".to_string(), json!(obj));
                context_map.insert("schema_uuid".to_string(), json!(sch));
                context_map.insert("content_type".to_string(), json!(ctype));
                context_map.insert("kid".to_string(), json!(kid));
                context_map.insert("alg".to_string(), json!(alg));
            }
            "wrap-database-key-v1" | "wrap-record-key-v1" => {
                let wkid = tc.input.wrapped_kid.expect("Missing wrapped_kid");
                let wgkid = tc.input.wrapping_kid.expect("Missing wrapping_kid");

                context_map.insert("wrapped_kid".to_string(), json!(wkid));
                context_map.insert("wrapping_kid".to_string(), json!(wgkid));
            }
            _ => panic!("Unknown or unsupported policy: {}", tc.policy),
        }

        let context_val = Value::Object(context_map);
        let canonical_string = canonicalize(&context_val).expect("JCS canonicalization failed");

        if let Some(expected_string) = &tc.expected_string {
            assert_eq!(
                &canonical_string, expected_string,
                "Expected string mismatch for {}",
                tc.name
            );
        }

        let canonical_hex = hex::encode(canonical_string.as_bytes());
        assert_eq!(
            canonical_hex, tc.expected_hex,
            "Expected hex mismatch for {}",
            tc.name
        );
    }
}
