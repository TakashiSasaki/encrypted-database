use std::env;
use std::path::Path;
use vault_moukaeritai_work::open_read_only;

#[test]
fn test_external_fixture_read_only() {
    let db_path = env::var("VAULT_SQLITE_V1_FIXTURE_DB").unwrap_or_default();
    let passphrase = env::var("VAULT_SQLITE_V1_FIXTURE_PASSPHRASE").unwrap_or_default();
    let object_uuid = env::var("VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID").unwrap_or_default();
    let expected_payload_hex =
        env::var("VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX").unwrap_or_default();

    if db_path.is_empty()
        || passphrase.is_empty()
        || object_uuid.is_empty()
        || expected_payload_hex.is_empty()
    {
        println!(
            "External fixture integration test skipped: missing VAULT_SQLITE_V1_FIXTURE_* environment variables"
        );
        return;
    }

    let reader = open_read_only(Path::new(&db_path), &passphrase)
        .expect("Failed to open external fixture DB");

    let payload_bytes = match reader.decrypt_object(&object_uuid) {
        Err(vault_moukaeritai_work::sqlitev1_reader::ReaderError::NotFound(_))
            if expected_payload_hex == "DELETED" =>
        {
            return;
        }
        Err(e) if expected_payload_hex == "DELETED" => {
            panic!("Expected NotFound error for deleted object, got {:?}", e);
        }
        Ok(b) => b,
        Err(e) => panic!("Failed to decrypt object {}: {:?}", object_uuid, e),
    };

    if expected_payload_hex == "DELETED" {
        panic!("Expected object to be deleted but it was decrypted successfully");
    }

    let actual_payload_hex = hex::encode(payload_bytes);

    assert_eq!(
        actual_payload_hex, expected_payload_hex,
        "Decrypted payload hex mismatch"
    );
}
