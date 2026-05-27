use std::env;
use std::path::Path;
use vault_moukaeritai_work::{ReaderError, open_read_only};

#[test]
fn test_external_fixture_read_only() {
    let db_path = env::var("VAULT_SQLITE_V1_FIXTURE_DB").unwrap_or_default();
    let passphrase = env::var("VAULT_SQLITE_V1_FIXTURE_PASSPHRASE").unwrap_or_default();
    let object_uuid = env::var("VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID").unwrap_or_default();
    let expected_payload_hex =
        env::var("VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX").unwrap_or_default();
    let expect_not_found =
        env::var("VAULT_SQLITE_V1_FIXTURE_EXPECT_NOT_FOUND").unwrap_or_default() == "1";

    if db_path.is_empty()
        || passphrase.is_empty()
        || object_uuid.is_empty()
        || (!expect_not_found && expected_payload_hex.is_empty())
    {
        println!(
            "External fixture integration test skipped: missing VAULT_SQLITE_V1_FIXTURE_* environment variables"
        );
        return;
    }

    let reader = open_read_only(Path::new(&db_path), &passphrase)
        .expect("Failed to open external fixture DB");

    let payload_result = reader.decrypt_object(&object_uuid);
    if expect_not_found {
        match payload_result {
            Err(ReaderError::NotFound(_)) => return,
            _ => panic!("Expected NotFound error"),
        }
    }

    let actual_payload_hex = hex::encode(payload_result.expect("Failed to decrypt object"));

    assert_eq!(
        actual_payload_hex, expected_payload_hex,
        "Decrypted payload hex mismatch"
    );
}
