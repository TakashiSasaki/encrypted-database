use aes_gcm::Aes256Gcm;
use aes_gcm::aead::{Aead, KeyInit, Payload};
use argon2::{Algorithm, Argon2, Params, Version};
use rusqlite::Connection;
use serde_json::json;
use std::fs;
use std::time::{SystemTime, UNIX_EPOCH};
use tempfile::tempdir;
use vault_moukaeritai_work::aad::{build_record_payload_v1, build_wrap_key_v1};
use vault_moukaeritai_work::jcs::canonicalize;
use vault_moukaeritai_work::{ReaderError, open_read_only};

fn encrypt_aead(key: &[u8], nonce: &[u8], pt: &[u8], aad: &[u8]) -> Vec<u8> {
    let cipher = Aes256Gcm::new_from_slice(key).unwrap();
    let nonce = aes_gcm::Nonce::from_slice(nonce);
    let payload = Payload { msg: pt, aad };
    cipher.encrypt(nonce, payload).unwrap()
}

// This fixture is a deterministic minimal reader fixture, not a writer implementation.
fn create_test_db(db_path: &str, passphrase: &str) -> String {
    let schema_sql =
        fs::read_to_string("../docs/backend/sqlite/schema.sql").expect("Failed to read schema.sql");

    let conn = Connection::open(db_path).unwrap();
    conn.execute_batch(&schema_sql).unwrap();

    conn.execute("PRAGMA application_id = 1447906135", [])
        .unwrap();
    conn.execute("PRAGMA user_version = 1", []).unwrap();

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
        ("database_uuid", "11111111-1111-4111-8111-111111111111"),
        ("created_at_ms", &now_ms_str),
        ("created_by_library", "rust-test"),
        ("created_by_version", "1.0"),
        ("sqlite_application_id", "1447906135"),
        ("sqlite_user_version", "1"),
        ("required_features", "[]"),
        ("optional_features", "[]"),
    ];

    for (p, v) in metadata {
        conn.execute(
            "INSERT INTO storage_metadata_tbl (property, value) VALUES (?1, ?2)",
            [p, v],
        )
        .unwrap();
    }

    let db_kid = "22222222-2222-4222-8222-222222222222";
    let unlock_kid = "33333333-3333-4333-8333-333333333333";
    let record_kid = "44444444-4444-4444-8444-444444444444";
    let object_uuid = "55555555-5555-4555-8555-555555555555";
    let schema_uuid = "66666666-6666-4666-8666-666666666666";

    let db_kek = vec![0x11; 32];
    let record_dek = vec![0x22; 32];

    conn.execute("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        [db_kid, "database_kek", "wrap_record_keys", "A256GCM", "active", &now_ms_str]).unwrap();
    conn.execute("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        [unlock_kid, "unlock_kek", "wrap_database_keys", "A256GCM", "active", &now_ms_str]).unwrap();
    conn.execute("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)",
        [record_kid, "record_dek", "encrypt_payload", "A256GCM", "active", &now_ms_str]).unwrap();

    let config = json!({
        "kdf": "argon2id",
        "profile": "argon2id-profile-v1",
        "salt": "QUJDREVGR0hJSktMTU5PUA", // base64url of "ABCDEFGHIJKLMNOP"
        "memory_kib": 65536,
        "iterations": 3,
        "parallelism": 1,
        "output_bytes": 32
    });
    let config_jcs = canonicalize(&config).unwrap();

    conn.execute("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?1, ?2, ?3, ?4)",
        [unlock_kid, "passphrase_argon2id", &config_jcs, "server"]).unwrap();

    let salt = b"ABCDEFGHIJKLMNOP";
    let mut unlock_kek = vec![0u8; 32];
    let params = Params::new(65536, 3, 1, Some(32)).unwrap();
    let argon2 = Argon2::new(Algorithm::Argon2id, Version::V0x13, params);
    argon2
        .hash_password_into(passphrase.as_bytes(), salt, &mut unlock_kek)
        .unwrap();

    let wrap_db_aad = build_wrap_key_v1("wrap-database-key-v1", db_kid, unlock_kid).unwrap();
    let wrap_db_nonce = vec![0xaa; 12];
    let wrapped_db_kek = encrypt_aead(&unlock_kek, &wrap_db_nonce, &db_kek, &wrap_db_aad);

    conn.execute("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
        ("77777777-7777-4777-8777-777777777777", db_kid, unlock_kid, 1, "key_wrap", "A256GCM", &wrap_db_nonce, &wrapped_db_kek, "wrap-database-key-v1", &now_ms_str)).unwrap();

    let wrap_rec_aad = build_wrap_key_v1("wrap-record-key-v1", record_kid, db_kid).unwrap();
    let wrap_rec_nonce = vec![0xbb; 12];
    let wrapped_rec_dek = encrypt_aead(&db_kek, &wrap_rec_nonce, &record_dek, &wrap_rec_aad);

    conn.execute("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)",
        ("88888888-8888-4888-8888-888888888888", record_kid, db_kid, 1, "key_wrap", "A256GCM", &wrap_rec_nonce, &wrapped_rec_dek, "wrap-record-key-v1", &now_ms_str)).unwrap();

    let payload = json!({"hello": "world", "v": 1});
    let payload_jcs = canonicalize(&payload).unwrap();
    let payload_aad = build_record_payload_v1(
        object_uuid,
        schema_uuid,
        "application/json",
        record_kid,
        "A256GCM",
    )
    .unwrap();
    let payload_nonce = vec![0xcc; 12];
    let ciphertext = encrypt_aead(
        &record_dek,
        &payload_nonce,
        payload_jcs.as_bytes(),
        &payload_aad,
    );

    conn.execute("INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)",
        (object_uuid, 1, "aead", schema_uuid, "application/json", "A256GCM", record_kid, &payload_nonce, &ciphertext, "record-payload-v1", &now_ms_str, &now_ms_str)).unwrap();

    object_uuid.to_string()
}

#[test]
fn test_reader_valid() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test.db");
    let passphrase = "my-secret-pass";
    let obj_uuid = create_test_db(db_path.to_str().unwrap(), passphrase);

    let reader = open_read_only(&db_path, passphrase).expect("Open failed");
    let payload = reader.decrypt_object(&obj_uuid).expect("Decrypt failed");

    let payload_str = String::from_utf8(payload).unwrap();
    assert_eq!(payload_str, r#"{"hello":"world","v":1}"#);
}

#[test]
fn test_reader_wrong_passphrase() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test.db");
    let passphrase = "my-secret-pass";
    create_test_db(db_path.to_str().unwrap(), passphrase);

    let err = open_read_only(&db_path, "wrong-pass").unwrap_err();
    match err {
        ReaderError::AuthenticationFailure => (),
        _ => panic!("Expected AuthenticationFailure, got {:?}", err),
    }
}

#[test]
fn test_reader_object_not_found() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test.db");
    let passphrase = "my-secret-pass";
    create_test_db(db_path.to_str().unwrap(), passphrase);

    let reader = open_read_only(&db_path, passphrase).expect("Open failed");
    let err = reader
        .decrypt_object("99999999-9999-4999-8999-999999999999")
        .unwrap_err();
    match err {
        ReaderError::ObjectNotFound => (),
        _ => panic!("Expected ObjectNotFound, got {:?}", err),
    }
}
