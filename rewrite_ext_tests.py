import sys

# Patch Go
with open("go/internal/sqlitev1/reader_external_fixture_test.go", "r") as f:
    go_content = f.read()

go_content = go_content.replace('"os"', '"errors"\n\t"os"')
go_content = go_content.replace('payloadBytes, err := reader.DecryptObject(objectUUID)\n\tif err != nil {', 'payloadBytes, err := reader.DecryptObject(objectUUID)\n\n\tif expectedPayloadHex == "DELETED" {\n\t\tif !errors.Is(err, ErrNotFound) {\n\t\t\tt.Fatalf("Expected ErrNotFound for deleted object, got: %v", err)\n\t\t}\n\t\treturn\n\t}\n\n\tif err != nil {')

with open("go/internal/sqlitev1/reader_external_fixture_test.go", "w") as f:
    f.write(go_content)

# Patch Rust
with open("rust/tests/sqlitev1_external_fixture.rs", "r") as f:
    rust_content = f.read()

rust_content = rust_content.replace('    let payload_bytes = match reader.decrypt_object(&object_uuid) {\n        Ok(b) => b,\n        Err(e) => panic!("Failed to decrypt object {}: {:?}", object_uuid, e),\n    };', '    let payload_bytes = match reader.decrypt_object(&object_uuid) {\n        Err(vault_moukaeritai_work::sqlitev1_reader::ReaderError::NotFound(_)) if expected_payload_hex == "DELETED" => {\n            return;\n        }\n        Err(e) if expected_payload_hex == "DELETED" => {\n            panic!("Expected NotFound error for deleted object, got {:?}", e);\n        }\n        Ok(b) => b,\n        Err(e) => panic!("Failed to decrypt object {}: {:?}", object_uuid, e),\n    };')

with open("rust/tests/sqlitev1_external_fixture.rs", "w") as f:
    f.write(rust_content)
