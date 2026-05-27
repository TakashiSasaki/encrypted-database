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
