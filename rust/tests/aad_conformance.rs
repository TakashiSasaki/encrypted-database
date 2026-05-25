use serde::Deserialize;
use vault_moukaeritai_work::{
    aad::{build_record_payload_v1, build_wrap_key_v1},
    vectors::test_vector_path,
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
    let path =
        test_vector_path("aad/aad-policies-v1.json").expect("Failed to locate AAD vector file");

    let content = std::fs::read_to_string(&path).expect("Failed to read AAD vector file");

    let vectors: Vec<AADVector> =
        serde_json::from_str(&content).expect("Failed to parse AAD JSON array");

    for tc in vectors {
        let canonical_bytes = match tc.policy.as_str() {
            "record-payload-v1" => {
                let obj = tc.input.object_uuid.expect("Missing object_uuid");
                let sch = tc.input.schema_uuid.expect("Missing schema_uuid");
                let ctype = tc.input.content_type.expect("Missing content_type");
                let kid = tc.input.kid.expect("Missing kid");
                let alg = tc.input.alg.expect("Missing alg");
                build_record_payload_v1(&obj, &sch, &ctype, &kid, &alg).expect("AAD builder failed")
            }
            "wrap-database-key-v1" | "wrap-record-key-v1" => {
                let wkid = tc.input.wrapped_kid.expect("Missing wrapped_kid");
                let wgkid = tc.input.wrapping_kid.expect("Missing wrapping_kid");
                build_wrap_key_v1(&tc.policy, &wkid, &wgkid).expect("AAD builder failed")
            }
            _ => panic!("Unknown or unsupported policy: {}", tc.policy),
        };

        let canonical_string = String::from_utf8(canonical_bytes.clone()).expect("Invalid UTF-8");

        if let Some(expected_string) = &tc.expected_string {
            assert_eq!(
                &canonical_string, expected_string,
                "Expected string mismatch for {}",
                tc.name
            );
        }

        let canonical_hex = hex::encode(&canonical_bytes);
        assert_eq!(
            canonical_hex, tc.expected_hex,
            "Expected hex mismatch for {}",
            tc.name
        );
    }
}
