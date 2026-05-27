use serde_json::json;
use std::env;
use tempfile::tempdir;
use vault_moukaeritai_work::sqlitev1_writer::create_new;

#[test]
fn test_writer_update_delete() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("test_update_delete.db");

    unsafe {
        env::set_var("VAULT_SCHEMA_SQL_PATH", "../docs/backend/sqlite/schema.sql");
    }

    let passphrase = "test-passphrase";
    let platform = "linux";

    let mut writer = create_new(&db_path, passphrase, platform).unwrap();

    let schema_uuid = "00000000-0000-4000-8000-000000000001";
    let content_type = "application/json";
    let payload1 = json!({"val": 1});
    let payload2 = json!({"val": 2});

    let obj_uuid = writer.store_payload(schema_uuid, content_type, &payload1).unwrap();

    writer.update_payload(&obj_uuid, schema_uuid, content_type, &payload2).unwrap();
    writer.delete_payload(&obj_uuid).unwrap();

    assert!(writer.delete_payload(&obj_uuid).is_err());
    assert!(writer.update_payload(&obj_uuid, schema_uuid, content_type, &payload2).is_err());
}
