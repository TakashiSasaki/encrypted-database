use base64::{Engine, engine::general_purpose::URL_SAFE_NO_PAD};

/// Decodes a base64url encoded string strictly without padding.
/// It rejects strings containing '=' padding characters or invalid URL-safe characters.
pub fn decode_strict(s: &str) -> Result<Vec<u8>, String> {
    if s.contains('=') {
        return Err("base64url string contains '=' padding, which is not allowed".to_string());
    }

    URL_SAFE_NO_PAD
        .decode(s)
        .map_err(|e| format!("Base64url decode error: {}", e))
}
