use crate::jcs::canonicalize;
use serde_json::{json, Value};

#[derive(Debug)]
pub enum AADError {
    MissingField(&'static str),
    UnsupportedPolicy(String),
    JcsError(String),
}

pub fn build_record_payload_v1(
    object_uuid: &str,
    schema_uuid: &str,
    content_type: &str,
    kid: &str,
    alg: &str,
) -> Result<Vec<u8>, AADError> {
    if object_uuid.is_empty() { return Err(AADError::MissingField("object_uuid")); }
    if schema_uuid.is_empty() { return Err(AADError::MissingField("schema_uuid")); }
    if content_type.is_empty() { return Err(AADError::MissingField("content_type")); }
    if kid.is_empty() { return Err(AADError::MissingField("kid")); }
    if alg.is_empty() { return Err(AADError::MissingField("alg")); }

    let mut map = serde_json::Map::new();
    map.insert("v".to_string(), json!(1));
    map.insert("aad_policy".to_string(), json!("record-payload-v1"));
    map.insert("object_uuid".to_string(), json!(object_uuid));
    map.insert("schema_uuid".to_string(), json!(schema_uuid));
    map.insert("content_type".to_string(), json!(content_type));
    map.insert("kid".to_string(), json!(kid));
    map.insert("alg".to_string(), json!(alg));

    let val = Value::Object(map);
    match canonicalize(&val) {
        Ok(s) => Ok(s.into_bytes()),
        Err(e) => Err(AADError::JcsError(e.to_string())),
    }
}

pub fn build_wrap_key_v1(
    policy: &str,
    wrapped_kid: &str,
    wrapping_kid: &str,
) -> Result<Vec<u8>, AADError> {
    if policy != "wrap-database-key-v1" && policy != "wrap-record-key-v1" {
        return Err(AADError::UnsupportedPolicy(policy.to_string()));
    }
    if wrapped_kid.is_empty() { return Err(AADError::MissingField("wrapped_kid")); }
    if wrapping_kid.is_empty() { return Err(AADError::MissingField("wrapping_kid")); }

    let mut map = serde_json::Map::new();
    map.insert("v".to_string(), json!(1));
    map.insert("aad_policy".to_string(), json!(policy));
    map.insert("wrapped_kid".to_string(), json!(wrapped_kid));
    map.insert("wrapping_kid".to_string(), json!(wrapping_kid));

    let val = Value::Object(map);
    match canonicalize(&val) {
        Ok(s) => Ok(s.into_bytes()),
        Err(e) => Err(AADError::JcsError(e.to_string())),
    }
}
