use crate::aad::{build_record_payload_v1, build_wrap_key_v1};
use crate::base64url::decode_strict;
use crate::jcs::canonicalize;
use crate::sqlitev1::{SqliteV1Error, validate_read_only};

use aes_gcm::Aes256Gcm;
use aes_gcm::aead::{Aead, KeyInit, Payload};
use argon2::{Algorithm, Argon2, Params, Version};
use rusqlite::{Connection, OpenFlags, OptionalExtension};
use serde_json::Value;
use std::path::Path;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum ReaderError {
    #[error("Metadata validation failed: {0}")]
    ValidationFailed(#[from] SqliteV1Error),
    #[error("Database error: {0}")]
    DbError(#[from] rusqlite::Error),
    #[error("Invalid format: {0}")]
    InvalidFormat(String),
    #[error("Invalid provider config: {0}")]
    InvalidProviderConfig(String),
    #[error("Unsupported provider or algorithm: {0}")]
    Unsupported(String),
    #[error("Authentication failure: wrong passphrase or decryption failed")]
    AuthenticationFailure,
    #[error("Not found: {0}")]
    NotFound(String),
    #[error("Invalid key status: {0}")]
    InvalidStatus(String),
    #[error("Invalid envelope: {0}")]
    InvalidEnvelope(String),
    #[error("Database locked or uninitialized")]
    Locked,
    #[error("Crypto error: {0}")]
    CryptoError(String),
}

#[derive(Debug)]
pub struct ReadOnlyReader {
    conn: Connection,
    active_db_kek: Vec<u8>,
    active_db_kid: String,
}

pub fn open_read_only(path: &Path, passphrase: &str) -> Result<ReadOnlyReader, ReaderError> {
    let _ = validate_read_only(path)?;

    let conn = Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_URI,
    )?;

    let mut reader = ReadOnlyReader {
        conn,
        active_db_kek: Vec::new(),
        active_db_kid: String::new(),
    };

    reader.unlock_database(passphrase)?;

    Ok(reader)
}

fn validate_argon2id_config(config_json: &str) -> Result<Vec<u8>, ReaderError> {
    let config: Value = serde_json::from_str(config_json)
        .map_err(|_| ReaderError::InvalidProviderConfig("Invalid JSON".to_string()))?;

    let canonical_config = canonicalize(&config)
        .map_err(|e| ReaderError::InvalidProviderConfig(format!("JCS failed: {}", e)))?;

    if canonical_config != config_json {
        return Err(ReaderError::InvalidProviderConfig(
            "provider_config_json is not valid JCS canonical JSON".to_string(),
        ));
    }

    let kdf = config["kdf"].as_str().ok_or_else(|| {
        ReaderError::InvalidProviderConfig("Missing kdf".to_string())
    })?;
    let profile = config["profile"].as_str().ok_or_else(|| {
        ReaderError::InvalidProviderConfig("Missing profile".to_string())
    })?;

    if kdf != "argon2id" || profile != "argon2id-profile-v1" {
        return Err(ReaderError::Unsupported(
            "Unsupported KDF or profile".to_string(),
        ));
    }

    let mem_kib = config["memory_kib"]
        .as_u64()
        .ok_or_else(|| ReaderError::InvalidProviderConfig("Missing memory_kib".to_string()))?;
    let iter = config["iterations"]
        .as_u64()
        .ok_or_else(|| ReaderError::InvalidProviderConfig("Missing iterations".to_string()))?;
    let parallelism = config["parallelism"]
        .as_u64()
        .ok_or_else(|| ReaderError::InvalidProviderConfig("Missing parallelism".to_string()))?;
    let out_bytes = config["output_bytes"]
        .as_u64()
        .ok_or_else(|| ReaderError::InvalidProviderConfig("Missing output_bytes".to_string()))?;
    let salt_b64 = config["salt"]
        .as_str()
        .ok_or_else(|| ReaderError::InvalidProviderConfig("Missing salt".to_string()))?;

    if mem_kib != 65536 || iter != 3 || parallelism != 1 || out_bytes != 32 {
        return Err(ReaderError::InvalidProviderConfig(
            "Immutable profile-v1 parameter mismatch".to_string(),
        ));
    }

    let salt = decode_strict(salt_b64)
        .map_err(|e| ReaderError::InvalidProviderConfig(format!("Salt decode: {}", e)))?;

    if salt.len() != 16 {
        return Err(ReaderError::InvalidProviderConfig(
            "Salt length must be 16 bytes".to_string(),
        ));
    }

    Ok(salt)
}

impl ReadOnlyReader {
    fn unlock_database(&mut self, passphrase: &str) -> Result<(), ReaderError> {
        let mut stmt = self.conn.prepare(
            "SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1",
        )?;
        let db_kid: String = stmt
            .query_row([], |row| row.get(0))
            .optional()?
            .ok_or_else(|| {
                ReaderError::InvalidStatus("no active database KEK found".to_string())
            })?;

        let mut stmt = self.conn.prepare(
            "SELECT wrapping_kid, nonce, wrapped_key, aad_policy, wrap_alg, envelope_v, envelope_type FROM wrapped_key_tbl WHERE wrapped_kid = ?",
        )?;
        let mut rows = stmt.query([&db_kid])?;

        let mut unwrapped = false;
        while let Some(row) = rows.next()? {
            let wrapping_kid: String = row.get(0)?;
            let nonce: Vec<u8> = row.get(1)?;
            let wrapped_key: Vec<u8> = row.get(2)?;
            let aad_policy: String = row.get(3)?;
            let wrap_alg: String = row.get(4)?;
            let envelope_v: i64 = row.get(5)?;
            let envelope_type: String = row.get(6)?;

            if wrap_alg != "A256GCM" {
                continue;
            }
            if envelope_v != 1 {
                continue;
            }
            if envelope_type != "key_wrap" {
                continue;
            }

            let mut unlock_stmt = self.conn.prepare(
                "SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?",
            )?;
            let unlock_row = unlock_stmt
                .query_row([&wrapping_kid], |r| {
                    Ok((r.get::<_, String>(0)?, r.get::<_, String>(1)?))
                })
                .optional()?;

            if let Some((provider, config_json)) = unlock_row {
                if provider == "passphrase_argon2id" {
                    let salt = validate_argon2id_config(&config_json)?;

                    let mut unlock_kek = vec![0u8; 32];
                    let params = Params::new(65536, 3, 1, Some(32))
                        .map_err(|e| ReaderError::CryptoError(format!("Argon2 params: {}", e)))?;
                    let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);

                    argon2
                        .hash_password_into(passphrase.as_bytes(), &salt, &mut unlock_kek)
                        .map_err(|e| ReaderError::CryptoError(format!("Argon2 hash: {}", e)))?;

                    if let Ok(wrap_aad) = build_wrap_key_v1(&aad_policy, &db_kid, &wrapping_kid) {
                        if let Ok(db_kek_bytes) =
                            self.decrypt_aead(&unlock_kek, &nonce, &wrapped_key, &wrap_aad)
                        {
                            if db_kek_bytes.len() != 32 {
                                return Err(ReaderError::InvalidEnvelope(
                                    "Unwrapped db_kek must be 32 bytes".to_string(),
                                ));
                            }
                            self.active_db_kek = db_kek_bytes;
                            self.active_db_kid = db_kid.clone();
                            unwrapped = true;
                            break;
                        }
                    }
                }
            }
        }

        if !unwrapped {
            return Err(ReaderError::AuthenticationFailure);
        }

        Ok(())
    }

    pub fn decrypt_object(&self, object_uuid: &str) -> Result<Vec<u8>, ReaderError> {
        if self.active_db_kek.is_empty() {
            return Err(ReaderError::AuthenticationFailure);
        }

        let mut stmt = self.conn.prepare(
            "SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy \
             FROM encrypted_object_tbl WHERE object_uuid = ?",
        )?;

        let obj_row = stmt
            .query_row([object_uuid], |row| {
                Ok((
                    row.get::<_, String>(0)?,
                    row.get::<_, String>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, Vec<u8>>(4)?,
                    row.get::<_, Vec<u8>>(5)?,
                    row.get::<_, String>(6)?,
                ))
            })
            .optional()?
            .ok_or_else(|| ReaderError::NotFound(object_uuid.to_string()))?;

        let (
            schema_uuid,
            content_type,
            alg,
            record_kid,
            nonce_payload,
            ciphertext,
            payload_aad_policy,
        ) = obj_row;

        if alg != "A256GCM" {
            return Err(ReaderError::Unsupported(format!(
                "Unsupported algorithm: {}",
                alg
            )));
        }
        if payload_aad_policy != "record-payload-v1" {
            return Err(ReaderError::Unsupported(format!(
                "Unsupported payload AAD policy: {}",
                payload_aad_policy
            )));
        }
        if nonce_payload.len() != 12 {
            return Err(ReaderError::InvalidEnvelope(format!(
                "Payload nonce length {}",
                nonce_payload.len()
            )));
        }
        if ciphertext.len() < 16 {
            return Err(ReaderError::InvalidEnvelope(format!(
                "Payload ciphertext length {}",
                ciphertext.len()
            )));
        }

        let mut status_stmt = self
            .conn
            .prepare("SELECT status FROM key_tbl WHERE kid = ? AND key_class = 'record_dek'")?;
        let record_dek_status: String = status_stmt
            .query_row([&record_kid], |row| row.get(0))
            .optional()?
            .ok_or_else(|| ReaderError::NotFound(format!("record DEK {} not found", record_kid)))?;

        if record_dek_status != "active" {
            return Err(ReaderError::InvalidStatus(
                "record DEK must be active".to_string(),
            ));
        }

        let mut stmt = self.conn.prepare(
            "SELECT nonce, wrapped_key, aad_policy, wrap_alg, envelope_v, envelope_type \
             FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?",
        )?;

        let wrap_row = stmt
            .query_row([&record_kid, &self.active_db_kid], |row| {
                Ok((
                    row.get::<_, Vec<u8>>(0)?,
                    row.get::<_, Vec<u8>>(1)?,
                    row.get::<_, String>(2)?,
                    row.get::<_, String>(3)?,
                    row.get::<_, i64>(4)?,
                    row.get::<_, String>(5)?,
                ))
            })
            .optional()?
            .ok_or_else(|| ReaderError::NotFound("record DEK wrap info not found".to_string()))?;

        let (nonce_wrap, wrapped_record_dek, wrap_aad_policy, wrap_alg, envelope_v, envelope_type) =
            wrap_row;

        if wrap_alg != "A256GCM" {
            return Err(ReaderError::Unsupported(format!(
                "Unsupported wrap algorithm: {}",
                wrap_alg
            )));
        }
        if envelope_v != 1 {
            return Err(ReaderError::Unsupported(format!(
                "Unsupported envelope version: {}",
                envelope_v
            )));
        }
        if envelope_type != "key_wrap" {
            return Err(ReaderError::Unsupported(format!(
                "Unsupported envelope type: {}",
                envelope_type
            )));
        }
        if nonce_wrap.len() != 12 {
            return Err(ReaderError::InvalidEnvelope(format!(
                "Wrap nonce length {}",
                nonce_wrap.len()
            )));
        }
        if wrapped_record_dek.len() < 16 {
            return Err(ReaderError::InvalidEnvelope(format!(
                "Wrapped record dek length {}",
                wrapped_record_dek.len()
            )));
        }

        let wrap_aad_bytes = build_wrap_key_v1(&wrap_aad_policy, &record_kid, &self.active_db_kid)
            .map_err(|e| ReaderError::CryptoError(format!("Wrap AAD build: {:?}", e)))?;

        let record_dek_bytes = self.decrypt_aead(
            &self.active_db_kek,
            &nonce_wrap,
            &wrapped_record_dek,
            &wrap_aad_bytes,
        )?;

        if record_dek_bytes.len() != 32 {
            return Err(ReaderError::InvalidEnvelope(
                "Unwrapped record DEK must be 32 bytes".to_string(),
            ));
        }

        let payload_aad_bytes =
            build_record_payload_v1(object_uuid, &schema_uuid, &content_type, &record_kid, &alg)
                .map_err(|e| ReaderError::CryptoError(format!("Payload AAD build: {:?}", e)))?;

        let payload_bytes = self.decrypt_aead(
            &record_dek_bytes,
            &nonce_payload,
            &ciphertext,
            &payload_aad_bytes,
        )?;

        Ok(payload_bytes)
    }

    fn decrypt_aead(
        &self,
        key: &[u8],
        nonce: &[u8],
        ciphertext_and_tag: &[u8],
        aad: &[u8],
    ) -> Result<Vec<u8>, ReaderError> {
        let cipher = Aes256Gcm::new_from_slice(key)
            .map_err(|_| ReaderError::CryptoError("Invalid key length".to_string()))?;

        if nonce.len() != 12 {
            return Err(ReaderError::InvalidEnvelope(format!(
                "Invalid nonce length: {}",
                nonce.len()
            )));
        }
        let nonce = aes_gcm::Nonce::from_slice(nonce);

        let payload = Payload {
            msg: ciphertext_and_tag,
            aad,
        };

        cipher
            .decrypt(nonce, payload)
            .map_err(|_| ReaderError::AuthenticationFailure)
    }
}
