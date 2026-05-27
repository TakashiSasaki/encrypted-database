import sys

# Patch Rust
with open("rust/tests/sqlitev1_external_fixture.rs", "r") as f:
    rust_content = f.read()

old_decrypt = '''    let payload_bytes = reader
        .decrypt_object(&object_uuid)
        .expect("Failed to decrypt object");'''

new_decrypt = '''    let payload_bytes = match reader.decrypt_object(&object_uuid) {
        Err(vault_moukaeritai_work::sqlitev1_reader::ReaderError::NotFound(_)) if expected_payload_hex == "DELETED" => {
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
    }'''

rust_content = rust_content.replace(old_decrypt, new_decrypt)

with open("rust/tests/sqlitev1_external_fixture.rs", "w") as f:
    f.write(rust_content)
