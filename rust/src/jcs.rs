use serde_json::Value;

use thiserror::Error;

#[derive(Error, Debug)]
pub enum JcsError {
    #[error("Unsupported JCS value: {0}")]
    UnsupportedValue(String),
}

/// Returns the JCS (RFC 8785) canonicalized JSON string representation of a value.
/// NOTE: This is a minimal implementation targeting the scope of AAD test vectors
/// and basic JCS validation. It may not fully support all edge cases of RFC 8785
/// (e.g., complex floating point numbers).
pub fn canonicalize(val: &Value) -> Result<String, JcsError> {
    match val {
        Value::Null => Ok("null".to_string()),
        Value::Bool(b) => Ok(if *b { "true".to_string() } else { "false".to_string() }),
        Value::String(s) => Ok(serialize_string(s)),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.to_string())
            } else if let Some(u) = n.as_u64() {
                Ok(u.to_string())
            } else if let Some(f) = n.as_f64() {
                // If it's a whole number, format as integer
                if f.fract() == 0.0 {
                    Ok(format!("{:.0}", f))
                } else {
                    Err(JcsError::UnsupportedValue("fractional float formatting not fully implemented".to_string()))
                }
            } else {
                Err(JcsError::UnsupportedValue("unknown number format".to_string()))
            }
        }
        Value::Array(arr) => {
            let mut out = String::new();
            out.push('[');
            for (i, item) in arr.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push_str(&canonicalize(item)?);
            }
            out.push(']');
            Ok(out)
        }
        Value::Object(obj) => {
            // Sort keys by UTF-16 code units
            let mut keys: Vec<&String> = obj.keys().collect();
            keys.sort_by(|a, b| compare_utf16(a, b));

            let mut out = String::new();
            out.push('{');
            for (i, k) in keys.iter().enumerate() {
                if i > 0 {
                    out.push(',');
                }
                out.push_str(&serialize_string(k));
                out.push(':');
                out.push_str(&canonicalize(obj.get(*k).unwrap())?);
            }
            out.push('}');
            Ok(out)
        }
    }
}

fn compare_utf16(s1: &str, s2: &str) -> std::cmp::Ordering {
    let u1: Vec<u16> = s1.encode_utf16().collect();
    let u2: Vec<u16> = s2.encode_utf16().collect();
    u1.cmp(&u2)
}

fn serialize_string(s: &str) -> String {
    let mut out = String::new();
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\x08' => out.push_str("\\b"),
            '\x0c' => out.push_str("\\f"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            _ if c < '\x20' => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            _ => out.push(c),
        }
    }
    out.push('"');
    out
}
