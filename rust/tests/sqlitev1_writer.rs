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
