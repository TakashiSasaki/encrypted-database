use rusqlite::Connection;
use serde_json::json;
use tempfile::tempdir;
use vault_moukaeritai_work::sqlitev1::validate_read_only;
use vault_moukaeritai_work::sqlitev1_reader::open_read_only;
use vault_moukaeritai_work::sqlitev1_writer::create_new;

#[test]
fn test_writer_roundtrip() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_writer.db");
    let passphrase = "test-passphrase";
    let platform = "linux";

    // 1. Create New Database
    let writer = create_new(&db_path, passphrase, platform).expect("Failed to create new db");

    // 2. Store Payload
    let schema_uuid = "00000000-0000-4000-8000-000000000001";
    let content_type = "application/json";
    let payload = json!({
        "hello": "world",
        "value": 42
    });

    let mut writer = writer;
    let obj_uuid = writer
        .store_payload(schema_uuid, content_type, &payload)
        .expect("Failed to store payload");

    writer.close().expect("Failed to close writer");

    // 3. Open Read Only and Validate
    let val_res = validate_read_only(&db_path).expect("Failed to validate DB");
    assert!(!val_res.database_uuid.is_empty());

    let reader = open_read_only(&db_path, passphrase).expect("Failed to open reader");

    // 4. Decrypt Object
    let decrypted_bytes = reader
        .decrypt_object(&obj_uuid)
        .expect("Failed to decrypt object");

    let expected_str = r#"{"hello":"world","value":42}"#;
    assert_eq!(String::from_utf8(decrypted_bytes).unwrap(), expected_str);

    // 5. Wrong Passphrase
    let bad_reader = open_read_only(&db_path, "wrong-passphrase");
    assert!(bad_reader.is_err());
}

#[test]
fn test_create_new_applies_pragmas() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_writer_pragma.db");

    let writer = create_new(&db_path, "test-passphrase", "linux").expect("Failed to create new db");
    writer.close().expect("Failed to close writer");

    let conn = Connection::open(&db_path).unwrap();

    let page_size: i64 = conn
        .query_row("PRAGMA page_size", [], |row| row.get(0))
        .unwrap();
    assert_eq!(page_size, 4096);

    let auto_vacuum: i64 = conn
        .query_row("PRAGMA auto_vacuum", [], |row| row.get(0))
        .unwrap();
    assert_eq!(auto_vacuum, 0);

    let journal_mode: String = conn
        .query_row("PRAGMA journal_mode", [], |row| row.get(0))
        .unwrap();
    assert_eq!(journal_mode, "wal");

    let synchronous: i64 = conn
        .query_row("PRAGMA synchronous", [], |row| row.get(0))
        .unwrap();
    assert!(synchronous == 1 || synchronous == 2);
}

#[test]
fn test_writer_negative_cases() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_writer_negative.db");
    let passphrase = "test-passphrase";

    // Empty passphrase
    assert!(create_new(&dir.path().join("empty_pass.db"), "", "linux").is_err());

    // Unknown platform
    assert!(
        create_new(
            &dir.path().join("unknown_platform.db"),
            passphrase,
            "unknown_platform"
        )
        .is_err()
    );

    // Valid creation
    let mut writer = create_new(&db_path, passphrase, "linux").expect("Failed to create new db");

    // Invalid schema_uuid
    let payload = json!({});
    assert!(
        writer
            .store_payload("invalid-uuid", "application/json", &payload)
            .is_err()
    );

    // Invalid content_type
    assert!(
        writer
            .store_payload(
                "00000000-0000-4000-8000-000000000001",
                "invalid_type",
                &payload
            )
            .is_err()
    );
}

#[test]
fn test_writer_multiple_payloads() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_writer_multi.db");
    let passphrase = "test-passphrase";
    let platform = "linux";

    let mut writer = create_new(&db_path, passphrase, platform).expect("Failed to create new db");

    let schema_uuid = "00000000-0000-4000-8000-000000000001";
    let content_type = "application/json";

    let mut uuids = Vec::new();
    for i in 0..5 {
        let payload = json!({ "index": i });
        let obj_uuid = writer
            .store_payload(schema_uuid, content_type, &payload)
            .expect("Failed to store payload");
        uuids.push(obj_uuid);
    }

    writer.close().expect("Failed to close writer");

    let reader = open_read_only(&db_path, passphrase).expect("Failed to open reader");

    for obj_uuid in uuids {
        assert!(reader.decrypt_object(&obj_uuid).is_ok());
    }
}

#[test]
fn test_writer_update_payload_roundtrip_and_timestamps() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_writer_update.db");
    let passphrase = "test-passphrase";
    let mut writer = create_new(&db_path, passphrase, "linux").expect("Failed to create db");

    let schema_uuid = "00000000-0000-4000-8000-000000000001";
    let content_type = "application/json";
    let obj_uuid = writer
        .store_payload(schema_uuid, content_type, &json!({"v": 1}))
        .expect("store failed");

    let conn = Connection::open(&db_path).unwrap();
    let (created_before, updated_before): (i64, i64) = conn
        .query_row(
            "SELECT created_at_ms, updated_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?1",
            [&obj_uuid],
            |r| Ok((r.get(0)?, r.get(1)?)),
        )
        .unwrap();

    std::thread::sleep(std::time::Duration::from_millis(2));
    writer
        .update_payload(
            &obj_uuid,
            "00000000-0000-4000-8000-000000000002",
            "application/merge-patch+json",
            &json!({"v": 2, "hello": "world"}),
        )
        .expect("update failed");
    writer.close().unwrap();

    let (created_after, updated_after, schema_after, content_after): (i64, i64, String, String) =
        conn.query_row(
            "SELECT created_at_ms, updated_at_ms, schema_uuid, content_type FROM encrypted_object_tbl WHERE object_uuid = ?1",
            [&obj_uuid],
            |r| Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get(3)?)),
        ).unwrap();
    assert_eq!(
        created_after, created_before,
        "created_at_ms must be preserved"
    );
    assert!(updated_after > updated_before, "updated_at_ms must advance");
    assert_eq!(schema_after, "00000000-0000-4000-8000-000000000002");
    assert_eq!(content_after, "application/merge-patch+json");

    let reader = open_read_only(&db_path, passphrase).expect("reader open failed");
    let plaintext = reader.decrypt_object(&obj_uuid).expect("decrypt failed");
    assert_eq!(
        String::from_utf8(plaintext).unwrap(),
        r#"{"hello":"world","v":2}"#
    );
}

#[test]
fn test_writer_delete_payload_only_deletes_object_row() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_writer_delete.db");
    let passphrase = "test-passphrase";
    let mut writer = create_new(&db_path, passphrase, "linux").expect("Failed to create db");

    let obj_uuid = writer
        .store_payload(
            "00000000-0000-4000-8000-000000000001",
            "application/json",
            &json!({"x": 1}),
        )
        .expect("store failed");

    let conn = Connection::open(&db_path).unwrap();
    let key_count_before: i64 = conn
        .query_row("SELECT COUNT(*) FROM key_tbl", [], |r| r.get(0))
        .unwrap();
    let wrapped_count_before: i64 = conn
        .query_row("SELECT COUNT(*) FROM wrapped_key_tbl", [], |r| r.get(0))
        .unwrap();
    let unlock_count_before: i64 = conn
        .query_row("SELECT COUNT(*) FROM unlock_kek_tbl", [], |r| r.get(0))
        .unwrap();

    writer.delete_payload(&obj_uuid).expect("delete failed");
    writer.close().unwrap();

    let object_count_after: i64 = conn
        .query_row(
            "SELECT COUNT(*) FROM encrypted_object_tbl WHERE object_uuid = ?1",
            [&obj_uuid],
            |r| r.get(0),
        )
        .unwrap();
    assert_eq!(object_count_after, 0);

    let key_count_after: i64 = conn
        .query_row("SELECT COUNT(*) FROM key_tbl", [], |r| r.get(0))
        .unwrap();
    let wrapped_count_after: i64 = conn
        .query_row("SELECT COUNT(*) FROM wrapped_key_tbl", [], |r| r.get(0))
        .unwrap();
    let unlock_count_after: i64 = conn
        .query_row("SELECT COUNT(*) FROM unlock_kek_tbl", [], |r| r.get(0))
        .unwrap();
    assert_eq!(key_count_after, key_count_before);
    assert_eq!(wrapped_count_after, wrapped_count_before);
    assert_eq!(unlock_count_after, unlock_count_before);
}

#[test]
fn test_writer_update_delete_validation_and_not_found() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_writer_update_delete_negative.db");
    let mut writer = create_new(&db_path, "test-passphrase", "linux").expect("create failed");
    let payload = json!({"ok": true});

    assert!(
        writer
            .update_payload(
                "invalid-uuid",
                "00000000-0000-4000-8000-000000000001",
                "application/json",
                &payload
            )
            .is_err()
    );
    assert!(
        writer
            .update_payload(
                "00000000-0000-4000-8000-000000000010",
                "invalid-uuid",
                "application/json",
                &payload
            )
            .is_err()
    );
    assert!(
        writer
            .update_payload(
                "00000000-0000-4000-8000-000000000010",
                "00000000-0000-4000-8000-000000000001",
                "invalid_type",
                &payload
            )
            .is_err()
    );
    assert!(
        writer
            .update_payload(
                "00000000-0000-4000-8000-000000000010",
                "00000000-0000-4000-8000-000000000001",
                "application/",
                &payload
            )
            .is_err()
    );
    assert!(
        writer
            .update_payload(
                "00000000-0000-4000-8000-000000000010",
                "00000000-0000-4000-8000-000000000001",
                "application/\u{0007}json",
                &payload
            )
            .is_err()
    );
    assert!(writer.delete_payload("invalid-uuid").is_err());

    assert!(
        writer
            .update_payload(
                "00000000-0000-4000-8000-000000000010",
                "00000000-0000-4000-8000-000000000001",
                "application/json",
                &payload
            )
            .is_err()
    );
    assert!(
        writer
            .delete_payload("00000000-0000-4000-8000-000000000010")
            .is_err()
    );
}
