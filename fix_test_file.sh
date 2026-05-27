#!/bin/bash
cat << 'INNER_EOF' > rust/tests/sqlitev1_writer.rs
use serde_json::json;
use std::env;
use tempfile::tempdir;
use vault_moukaeritai_work::sqlitev1_reader::open_read_only;
use vault_moukaeritai_work::sqlitev1_writer::{create_new, WriterError};

#[test]
fn test_writer_roundtrip() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_roundtrip.db");
    let passphrase = "test-passphrase";
    let platform = "linux";

    // Set schema path explicitly for testing if running from root
    env::set_var("VAULT_SCHEMA_SQL_PATH", "../docs/backend/sqlite/schema.sql");

    // 1. Create new database
    let mut writer = create_new(&db_path, passphrase, platform).expect("Failed to create DB");

    // 2. Store payload
    let schema_uuid = "00000000-0000-4000-8000-000000000001";
    let content_type = "application/json";
    let payload = json!({"key": "value", "num": 42});

    let obj_uuid = writer
        .store_payload(schema_uuid, content_type, &payload)
        .expect("Failed to store payload");

    assert_eq!(obj_uuid.len(), 36);

    // Close writer
    writer.close().expect("Failed to close writer");

    // 3. Read and verify using the existing reader
    let mut reader = open_read_only(&db_path).expect("Failed to open reader");
    reader.unlock(passphrase).expect("Failed to unlock DB");

    let decrypted = reader
        .decrypt_object(&obj_uuid)
        .expect("Failed to decrypt object");

    // Check payload (JCS canonical format)
    assert_eq!(decrypted, b"{\"key\":\"value\",\"num\":42}");
}

#[test]
fn test_writer_negative_cases() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_negative.db");
    let passphrase = "test-passphrase";
    let platform = "linux";

    env::set_var("VAULT_SCHEMA_SQL_PATH", "../docs/backend/sqlite/schema.sql");

    // Missing passphrase
    let err = create_new(&db_path, "", platform).unwrap_err();
    assert!(matches!(err, WriterError::RequirementError(_)));

    // Unknown platform
    let err2 = create_new(&db_path, passphrase, "unknown_platform").unwrap_err();
    assert!(matches!(err2, WriterError::UnsupportedPlatform(_)));

    // Valid create
    let mut writer = create_new(&db_path, passphrase, platform).unwrap();

    let valid_schema = "00000000-0000-4000-8000-000000000001";
    let valid_ct = "application/json";
    let payload = json!({});

    // Invalid schema UUID
    let err3 = writer.store_payload("invalid-uuid", valid_ct, &payload).unwrap_err();
    assert!(matches!(err3, WriterError::RequirementError(_)));

    // Invalid content type
    let err4 = writer.store_payload(valid_schema, "invalid", &payload).unwrap_err();
    assert!(matches!(err4, WriterError::RequirementError(_)));
}

#[test]
fn test_writer_multiple_payloads() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_multiple.db");
    let passphrase = "test-passphrase";
    let platform = "linux";

    env::set_var("VAULT_SCHEMA_SQL_PATH", "../docs/backend/sqlite/schema.sql");

    let mut writer = create_new(&db_path, passphrase, platform).unwrap();

    let mut uuids = vec![];
    for i in 0..5 {
        let obj_uuid = writer
            .store_payload(
                "00000000-0000-4000-8000-000000000001",
                "application/json",
                &json!({"index": i}),
            )
            .expect("Failed to store payload");
        uuids.push(obj_uuid);
    }

    writer.close().expect("Failed to close writer");

    let mut reader = open_read_only(&db_path).expect("Failed to open reader");
    reader.unlock(passphrase).expect("Failed to unlock DB");

    for obj_uuid in uuids {
        assert!(reader.decrypt_object(&obj_uuid).is_ok());
    }
}

#[test]
fn test_update_and_delete_payload() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_update_delete.db");
    let passphrase = "test-passphrase";
    let platform = "linux";

    env::set_var("VAULT_SCHEMA_SQL_PATH", "../docs/backend/sqlite/schema.sql");

    let mut writer = create_new(&db_path, passphrase, platform).unwrap();
    let schema_uuid = "00000000-0000-4000-8000-000000000001";
    let content_type = "application/json";
    let payload1 = json!({"msg": "hello"});

    let obj_uuid = writer
        .store_payload(schema_uuid, content_type, &payload1)
        .unwrap();

    let new_schema_uuid = "00000000-0000-4000-8000-000000000002";
    let payload2 = json!({"msg": "world"});

    writer.update_payload(&obj_uuid, new_schema_uuid, content_type, &payload2).unwrap();

    let mut reader = open_read_only(&db_path).unwrap();
    reader.unlock(passphrase).unwrap();
    let decrypted = reader.decrypt_object(&obj_uuid).unwrap();
    assert_eq!(decrypted, b"{\"msg\":\"world\"}");

    let fake_uuid = "00000000-0000-4000-8000-000000000003";
    assert!(matches!(writer.update_payload(fake_uuid, new_schema_uuid, content_type, &payload2), Err(vault_moukaeritai_work::sqlitev1_writer::WriterError::NotFound(_))));

    writer.delete_payload(&obj_uuid).unwrap();
    assert!(matches!(writer.delete_payload(fake_uuid), Err(vault_moukaeritai_work::sqlitev1_writer::WriterError::NotFound(_))));

    assert!(matches!(reader.decrypt_object(&obj_uuid), Err(vault_moukaeritai_work::sqlitev1_reader::ReaderError::NotFound(_))));
}
INNER_EOF
