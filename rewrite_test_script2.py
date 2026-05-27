import sys

with open("integration-tests/write-matrix/test_writer_matrix.sh", "r") as f:
    content = f.read()

go_run_old = '(cd "$ROOT_DIR/go" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$expected_payload_hex" go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly)'
go_run_new = '''if [ "$mode" == "delete" ]; then
            (cd "$ROOT_DIR/go" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="DELETED" go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly)
        else
            (cd "$ROOT_DIR/go" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$expected_payload_hex" go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly)
        fi'''

rust_run_old = '(cd "$ROOT_DIR/rust" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$expected_payload_hex" cargo test --test sqlitev1_external_fixture)'
rust_run_new = '''if [ "$mode" == "delete" ]; then
            (cd "$ROOT_DIR/rust" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="DELETED" cargo test --test sqlitev1_external_fixture)
        else
            (cd "$ROOT_DIR/rust" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$expected_payload_hex" cargo test --test sqlitev1_external_fixture)
        fi'''

content = content.replace(go_run_old, go_run_new)
content = content.replace(rust_run_old, rust_run_new)

with open("integration-tests/write-matrix/test_writer_matrix.sh", "w") as f:
    f.write(content)
