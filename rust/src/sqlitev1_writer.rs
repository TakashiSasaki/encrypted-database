use crate::aad::{build_record_payload_v1, build_wrap_key_v1};
use crate::jcs::canonicalize;
use aes_gcm::Aes256Gcm;
use aes_gcm::aead::{Aead, KeyInit, Payload};
use argon2::{Algorithm, Argon2, Params, Version};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use rusqlite::Connection;
use serde_json::json;
use std::env;
use std::fs;
use std::path::Path;
use std::time::{SystemTime, UNIX_EPOCH};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum WriterError {
    #[error("Database error: {0}")]
    DbError(#[from] rusqlite::Error),
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    #[error("Crypto error: {0}")]
    CryptoError(String),
    #[error("Unsupported platform: {0}")]
    UnsupportedPlatform(String),
    #[error("JCS error: {0}")]
    JcsError(String),
    #[error("Missing requirement: {0}")]
    RequirementError(String),
}

pub struct Writer {
    conn: Connection,
    active_db_kek: Vec<u8>,
    active_db_kid: String,
}

fn generate_random_bytes(len: usize) -> Result<Vec<u8>, WriterError> {
    let mut buf = vec![0u8; len];
    getrandom::getrandom(&mut buf)
        .map_err(|e| WriterError::CryptoError(format!("Failed to get random bytes: {}", e)))?;
    Ok(buf)
}

fn generate_uuid() -> Result<String, WriterError> {
    let mut uuid = generate_random_bytes(16)?;
    // Set UUID v4
    uuid[6] = (uuid[6] & 0x0f) | 0x40;
    // Set RFC4122 variant
    uuid[8] = (uuid[8] & 0x3f) | 0x80;
    Ok(format!(
        "{:02x}{:02x}{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}-{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}",
        uuid[0],
        uuid[1],
        uuid[2],
        uuid[3],
        uuid[4],
        uuid[5],
        uuid[6],
        uuid[7],
        uuid[8],
        uuid[9],
        uuid[10],
        uuid[11],
        uuid[12],
        uuid[13],
        uuid[14],
        uuid[15]
    ))
}

fn load_schema_sql() -> Result<String, WriterError> {
    let path = env::var("VAULT_SCHEMA_SQL_PATH").unwrap_or_else(|_| {
        if Path::new("docs/backend/sqlite/schema.sql").exists() {
            "docs/backend/sqlite/schema.sql".to_string()
        } else if Path::new("../docs/backend/sqlite/schema.sql").exists() {
            "../docs/backend/sqlite/schema.sql".to_string()
        } else if Path::new("../../docs/backend/sqlite/schema.sql").exists() {
            "../../docs/backend/sqlite/schema.sql".to_string()
        } else {
            "../../../docs/backend/sqlite/schema.sql".to_string()
        }
    });
    fs::read_to_string(path).map_err(WriterError::IoError)
}

pub fn create_new(path: &Path, passphrase: &str, platform: &str) -> Result<Writer, WriterError> {
    if passphrase.is_empty() {
        return Err(WriterError::RequirementError(
            "Passphrase must be a non-empty string".into(),
        ));
    }

    let schema_sql = load_schema_sql()?;

    let mut conn = Connection::open(path)?;

    // Set PRAGMA foreign_keys = ON before transaction
    conn.execute("PRAGMA foreign_keys = ON", [])?;

    let tx = conn.transaction()?;

    // Bootstrap schema inside transaction
    tx.execute_batch(&schema_sql)?;
    tx.execute("PRAGMA application_id = 1447906135", [])?;
    tx.execute("PRAGMA user_version = 1", [])?;

    // Validate platform
    {
        let mut stmt = tx.prepare("SELECT platform FROM platform_tbl WHERE platform = ?1")?;
        let platform_exists = stmt.exists([platform])?;
        if !platform_exists {
            return Err(WriterError::UnsupportedPlatform(platform.to_string()));
        }
    }

    let db_kek_bytes = generate_random_bytes(32)?;
    let db_kid = generate_uuid()?;

    let salt = generate_random_bytes(16)?;

    let mut unlock_kek_bytes = vec![0u8; 32];
    let params = Params::new(65536, 3, 1, Some(32))
        .map_err(|e| WriterError::CryptoError(format!("Argon2 params: {}", e)))?;
    let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
    argon2
        .hash_password_into(passphrase.as_bytes(), &salt, &mut unlock_kek_bytes)
        .map_err(|e| WriterError::CryptoError(format!("Argon2 hash: {}", e)))?;

    let unlock_kid = generate_uuid()?;

    let salt_b64 = URL_SAFE_NO_PAD.encode(&salt);
    let provider_config = json!({
        "kdf": "argon2id",
        "profile": "argon2id-profile-v1",
        "salt": salt_b64,
        "memory_kib": 65536,
        "iterations": 3,
        "parallelism": 1,
        "output_bytes": 32
    });

    let provider_config_json =
        canonicalize(&provider_config).map_err(|e| WriterError::JcsError(e.to_string()))?;

    let wrap_alg = "A256GCM";
    let aad_policy_name = "wrap-database-key-v1";
    let aad_bytes = build_wrap_key_v1(aad_policy_name, &db_kid, &unlock_kid)
        .map_err(|e| WriterError::CryptoError(format!("Wrap AAD build: {:?}", e)))?;

    let nonce = generate_random_bytes(12)?;

    let cipher = Aes256Gcm::new_from_slice(&unlock_kek_bytes)
        .map_err(|e| WriterError::CryptoError(format!("AES Key: {}", e)))?;
    let nonce_arr = aes_gcm::Nonce::from_slice(&nonce);
    let payload = Payload {
        msg: &db_kek_bytes,
        aad: &aad_bytes,
    };
    let wrapped_db_kek = cipher
        .encrypt(nonce_arr, payload)
        .map_err(|e| WriterError::CryptoError(format!("Encrypt error: {}", e)))?;

    let db_uuid = generate_uuid()?;
    let now_ms = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_millis() as i64;

    let now_ms_str = now_ms.to_string();
    let metadata = vec![
        ("storage_format_id", "vault.moukaeritai.work.storage"),
        ("format_major", "1"),
        ("format_minor", "0"),
        ("schema_version", "1"),
        ("database_uuid", &db_uuid),
        ("created_at_ms", &now_ms_str),
        ("created_by_library", "vault-rust"),
        ("created_by_version", "0.0.0-dev"),
        ("sqlite_application_id", "1447906135"),
        ("sqlite_user_version", "1"),
        ("required_features", "[]"),
        ("optional_features", "[]"),
    ];

    for (prop, val) in metadata {
        tx.execute(
            "INSERT INTO storage_metadata_tbl (property, value) VALUES (?1, ?2)",
            (prop, val),
        )?;
    }

    tx.execute(
        "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        (&db_kid, "database_kek", "wrap_record_keys", wrap_alg, "active", now_ms),
    )?;

    tx.execute(
        "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        (&unlock_kid, "unlock_kek", "wrap_database_keys", wrap_alg, "active", now_ms),
    )?;

    tx.execute(
        "INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?1, ?2, ?3, ?4)",
        (&unlock_kid, "passphrase_argon2id", &provider_config_json, platform),
    )?;

    let wrap_id = generate_uuid()?;
    tx.execute(
        "INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
        (wrap_id, &db_kid, &unlock_kid, 1, "key_wrap", wrap_alg, &nonce, &wrapped_db_kek, aad_policy_name, now_ms),
    )?;

    tx.commit()?;

    Ok(Writer {
        conn,
        active_db_kek: db_kek_bytes,
        active_db_kid: db_kid,
    })
}

impl Writer {
    pub fn store_payload(
        &mut self,
        schema_uuid: &str,
        content_type: &str,
        payload: &serde_json::Value,
    ) -> Result<String, WriterError> {
        if self.active_db_kek.is_empty() {
            return Err(WriterError::RequirementError("Database is locked".into()));
        }

        // Validate schema_uuid manually to avoid pulling in regex dependency / LazyLock which requires newer Rust
        let is_valid_uuid = schema_uuid.len() == 36
            && schema_uuid.chars().enumerate().all(|(i, c)| match i {
                8 | 13 | 18 | 23 => c == '-',
                14 => ('1'..='8').contains(&c),
                19 => ['8', '9', 'a', 'b'].contains(&c),
                _ => c.is_ascii_hexdigit() && (c.is_ascii_lowercase() || c.is_ascii_digit()),
            });

        if !is_valid_uuid {
            return Err(WriterError::RequirementError("Invalid schema_uuid".into()));
        }

        if content_type.is_empty() || !content_type.contains('/') {
            return Err(WriterError::RequirementError("Invalid content type".into()));
        }

        let object_uuid = generate_uuid()?;
        let record_dek_bytes = generate_random_bytes(32)?;
        let record_kid = generate_uuid()?;
        let alg = "A256GCM";

        let wrap_aad_policy = "wrap-record-key-v1";
        let wrap_aad_bytes =
            build_wrap_key_v1(wrap_aad_policy, &record_kid, &self.active_db_kid)
                .map_err(|e| WriterError::CryptoError(format!("Wrap AAD build: {:?}", e)))?;

        let nonce_wrap = generate_random_bytes(12)?;
        let cipher_wrap = Aes256Gcm::new_from_slice(&self.active_db_kek)
            .map_err(|e| WriterError::CryptoError(format!("AES Key: {}", e)))?;
        let nonce_wrap_arr = aes_gcm::Nonce::from_slice(&nonce_wrap);
        let payload_wrap = Payload {
            msg: &record_dek_bytes,
            aad: &wrap_aad_bytes,
        };
        let wrapped_record_dek = cipher_wrap
            .encrypt(nonce_wrap_arr, payload_wrap)
            .map_err(|e| WriterError::CryptoError(format!("Encrypt error: {}", e)))?;

        let payload_str =
            canonicalize(payload).map_err(|e| WriterError::JcsError(e.to_string()))?;
        let payload_bytes = payload_str.as_bytes();

        let payload_aad_policy = "record-payload-v1";
        let payload_aad_bytes =
            build_record_payload_v1(&object_uuid, schema_uuid, content_type, &record_kid, alg)
                .map_err(|e| WriterError::CryptoError(format!("Payload AAD build: {:?}", e)))?;

        let nonce_payload = generate_random_bytes(12)?;
        let cipher_payload = Aes256Gcm::new_from_slice(&record_dek_bytes)
            .map_err(|e| WriterError::CryptoError(format!("AES Key: {}", e)))?;
        let nonce_payload_arr = aes_gcm::Nonce::from_slice(&nonce_payload);
        let payload_encrypt = Payload {
            msg: payload_bytes,
            aad: &payload_aad_bytes,
        };
        let ciphertext = cipher_payload
            .encrypt(nonce_payload_arr, payload_encrypt)
            .map_err(|e| WriterError::CryptoError(format!("Encrypt error: {}", e)))?;

        let now_ms = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as i64;

        let wrap_id = generate_uuid()?;

        let tx = self.conn.transaction()?;

        tx.execute(
            "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
            (&record_kid, "record_dek", "encrypt_payload", alg, "active", now_ms),
        )?;

        tx.execute(
            "INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
            (&wrap_id, &record_kid, &self.active_db_kid, 1, "key_wrap", alg, &nonce_wrap, &wrapped_record_dek, wrap_aad_policy, now_ms),
        )?;

        tx.execute(
            "INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
            (&object_uuid, 1, "aead", schema_uuid, content_type, alg, &record_kid, &nonce_payload, &ciphertext, payload_aad_policy, now_ms, now_ms),
        )?;

        tx.commit()?;

        Ok(object_uuid)
    }

    pub fn close(self) -> Result<(), WriterError> {
        self.conn
            .close()
            .map_err(|(_, e)| WriterError::DbError(e))?;
        Ok(())
    }
}
