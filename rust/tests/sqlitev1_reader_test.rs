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
        ReaderError::NotFound(_) => (),
        _ => panic!("Expected NotFound, got {:?}", err),
    }
}

struct NegativeCase {
    name: &'static str,
    mutate: Box<dyn Fn(&Connection)>,
    expected_error: fn(&ReaderError) -> bool,
}

#[test]
fn test_reader_negative_cases() {
    let passphrase = "my-secret-pass";
    let db_kid = "22222222-2222-4222-8222-222222222222";
    let unlock_kid = "33333333-3333-4333-8333-333333333333";
    let record_kid = "44444444-4444-4444-8444-444444444444";
    let object_uuid = "55555555-5555-4555-8555-555555555555";

    let cases = vec![
        NegativeCase {
            name: "non-JCS provider_config_json",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?",
                    (r#"{"kdf": "argon2id", "profile": "argon2id-profile-v1", "salt": "QUJDREVGR0hJSktMTU5PUA", "memory_kib": 65536, "iterations": 3, "parallelism": 1, "output_bytes": 32 }"#, unlock_kid),
                ).unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidProviderConfig(_)),
        },
        NegativeCase {
            name: "profile mismatch",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?",
                    (r#"{"iterations":3,"kdf":"argon2id","memory_kib":65536,"output_bytes":32,"parallelism":1,"profile":"argon2id-profile-v2","salt":"QUJDREVGR0hJSktMTU5PUA"}"#, unlock_kid),
                ).unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "immutable parameter mismatch",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?",
                    (r#"{"iterations":4,"kdf":"argon2id","memory_kib":65536,"output_bytes":32,"parallelism":1,"profile":"argon2id-profile-v1","salt":"QUJDREVGR0hJSktMTU5PUA"}"#, unlock_kid),
                ).unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidProviderConfig(_)),
        },
        NegativeCase {
            name: "salt padding",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?",
                    (r#"{"iterations":3,"kdf":"argon2id","memory_kib":65536,"output_bytes":32,"parallelism":1,"profile":"argon2id-profile-v1","salt":"QUJDREVGR0hJSktMTU5PUA=="}"#, unlock_kid),
                ).unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidProviderConfig(_)),
        },
        NegativeCase {
            name: "salt invalid length",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?",
                    (r#"{"iterations":3,"kdf":"argon2id","memory_kib":65536,"output_bytes":32,"parallelism":1,"profile":"argon2id-profile-v1","salt":"QUJD"}"#, unlock_kid),
                ).unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidProviderConfig(_)),
        },
        NegativeCase {
            name: "unsupported unlock provider",
            mutate: Box::new(move |conn| {
                conn.execute("PRAGMA foreign_keys = OFF", []).unwrap();
                conn.execute(
                    "UPDATE unlock_kek_tbl SET unlock_provider = ? WHERE kid = ?",
                    ("unsupported_provider", unlock_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "tampered db wrapped key",
            mutate: Box::new(move |conn| {
                let mut wrapped_key: Vec<u8> = conn
                    .query_row(
                        "SELECT wrapped_key FROM wrapped_key_tbl WHERE wrapped_kid = ?",
                        [db_kid],
                        |row| row.get(0),
                    )
                    .unwrap();
                wrapped_key[0] ^= 0xff;
                conn.execute(
                    "UPDATE wrapped_key_tbl SET wrapped_key = ? WHERE wrapped_kid = ?",
                    (&wrapped_key, db_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::AuthenticationFailure),
        },
        NegativeCase {
            name: "tampered record wrapped key",
            mutate: Box::new(move |conn| {
                let mut wrapped_key: Vec<u8> = conn
                    .query_row(
                        "SELECT wrapped_key FROM wrapped_key_tbl WHERE wrapped_kid = ?",
                        [record_kid],
                        |row| row.get(0),
                    )
                    .unwrap();
                wrapped_key[0] ^= 0xff;
                conn.execute(
                    "UPDATE wrapped_key_tbl SET wrapped_key = ? WHERE wrapped_kid = ?",
                    (&wrapped_key, record_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::AuthenticationFailure),
        },
        NegativeCase {
            name: "tampered payload ciphertext",
            mutate: Box::new(move |conn| {
                let mut ciphertext: Vec<u8> = conn
                    .query_row(
                        "SELECT ciphertext FROM encrypted_object_tbl WHERE object_uuid = ?",
                        [object_uuid],
                        |row| row.get(0),
                    )
                    .unwrap();
                ciphertext[0] ^= 0xff;
                conn.execute(
                    "UPDATE encrypted_object_tbl SET ciphertext = ? WHERE object_uuid = ?",
                    (&ciphertext, object_uuid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::AuthenticationFailure),
        },
        NegativeCase {
            name: "tampered payload metadata (AAD mismatch)",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE encrypted_object_tbl SET content_type = ? WHERE object_uuid = ?",
                    ("text/plain", object_uuid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::AuthenticationFailure),
        },
        NegativeCase {
            name: "unsupported payload algorithm",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE encrypted_object_tbl SET alg = ? WHERE object_uuid = ?",
                    ("A128GCM", object_uuid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "unsupported payload aad policy",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE encrypted_object_tbl SET aad_policy = ? WHERE object_uuid = ?",
                    ("unsupported-policy", object_uuid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "unsupported wrap algorithm db_kek",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE wrapped_key_tbl SET wrap_alg = ? WHERE wrapped_kid = ?",
                    ("A128GCM", db_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "unsupported wrap algorithm record_dek",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE wrapped_key_tbl SET wrap_alg = ? WHERE wrapped_kid = ?",
                    ("A128GCM", record_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "unsupported envelope version db_kek",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE wrapped_key_tbl SET envelope_v = ? WHERE wrapped_kid = ?",
                    (2, db_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "unsupported envelope type db_kek",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE wrapped_key_tbl SET envelope_type = ? WHERE wrapped_kid = ?",
                    ("unsupported_type", db_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::Unsupported(_)),
        },
        NegativeCase {
            name: "inactive database_kek",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE key_tbl SET status = ? WHERE kid = ?",
                    ("decrypt_only", db_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidStatus(_)),
        },
        NegativeCase {
            name: "inactive record_dek",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE key_tbl SET status = ? WHERE kid = ?",
                    ("disabled", record_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidStatus(_)),
        },
        NegativeCase {
            name: "invalid db_kek wrap nonce length",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE wrapped_key_tbl SET nonce = ? WHERE wrapped_kid = ?",
                    (vec![0xaa; 11], db_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidEnvelope(_)),
        },
        NegativeCase {
            name: "invalid record_dek wrap nonce length",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE wrapped_key_tbl SET nonce = ? WHERE wrapped_kid = ?",
                    (vec![0xbb; 11], record_kid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidEnvelope(_)),
        },
        NegativeCase {
            name: "invalid payload nonce length",
            mutate: Box::new(move |conn| {
                conn.execute(
                    "UPDATE encrypted_object_tbl SET nonce = ? WHERE object_uuid = ?",
                    (vec![0xcc; 11], object_uuid),
                )
                .unwrap();
            }),
            expected_error: |e| matches!(e, ReaderError::InvalidEnvelope(_)),
        },
    ];

    for case in cases {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("test.db");
        create_test_db(db_path.to_str().unwrap(), passphrase);

        {
            let conn = Connection::open(&db_path).unwrap();
            conn.execute("PRAGMA ignore_check_constraints = ON", [])
                .unwrap();
            (case.mutate)(&conn);
        }

        match open_read_only(&db_path, passphrase) {
            Err(e) => {
                assert!(
                    (case.expected_error)(&e),
                    "Case '{}' failed during open: expected a certain error but got {:?}",
                    case.name,
                    e
                );
                continue;
            }
            Ok(reader) => match reader.decrypt_object(object_uuid) {
                Err(e) => {
                    assert!(
                        (case.expected_error)(&e),
                        "Case '{}' failed during decrypt: expected a certain error but got {:?}",
                        case.name,
                        e
                    );
                }
                Ok(_) => panic!("Case '{}' unexpectedly succeeded", case.name),
            },
        }
    }
}
