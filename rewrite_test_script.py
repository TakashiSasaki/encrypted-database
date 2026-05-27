import sys

with open("integration-tests/write-matrix/test_writer_matrix.sh", "r") as f:
    content = f.read()

content = content.replace('local write_cmd="$4"\n    local env_vars="$5"', 'local write_cmd="$4"\n    local env_vars="$5"\n    local mode="${6:-store}"')
content = content.replace('echo "=== Testing $writer_name Writer -> $reader_name Reader ==="', 'echo "=== Testing $writer_name Writer ($mode) -> $reader_name Reader ==="')
content = content.replace('rm -f "$db_path"\n\n    echo "Writing..."\n    # Set environment variables for schema path\n    local output\n    output=$(env $env_vars "$write_cmd" "$db_path" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_JSON")', 'if [ "$mode" == "store" ]; then\n        rm -f "$db_path"\n    fi\n\n    echo "Writing..."\n    local output\n    output=$(env $env_vars "$write_cmd" "$mode" "$db_path" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_JSON")')
content = content.replace('    elif [ "$reader_name" == "Python" ]; then\n        local py_out=$(python3 "$DIR/read_fixture_python.py" "$db_path" "$PASSPHRASE" "$obj_uuid")', '    elif [ "$reader_name" == "Python" ]; then\n        if [ "$mode" == "delete" ]; then\n            echo "Skipping Python reader NotFound verification for delete"\n        else\n            local py_out=$(python3 "$DIR/read_fixture_python.py" "$db_path" "$PASSPHRASE" "$obj_uuid")')
content = content.replace('            echo "Python Reader Failed: Expected $expected_payload_hex, got $actual_hex"\n            exit 1\n        fi\n    elif [ "$reader_name" == "Node" ]; then', '            echo "Python Reader Failed: Expected $expected_payload_hex, got $actual_hex"\n            exit 1\n        fi\n        fi\n    elif [ "$reader_name" == "Node" ]; then\n        if [ "$mode" == "delete" ]; then\n            echo "Skipping Node.js reader NotFound verification for delete"\n        else')
content = content.replace('            echo "Node Reader Failed: Expected $expected_payload_hex, got $actual_hex"\n            exit 1\n        fi\n    fi', '            echo "Node Reader Failed: Expected $expected_payload_hex, got $actual_hex"\n            exit 1\n        fi\n        fi\n    fi')

new_test_calls = """
run_all_modes() {
    local writer_name="$1"
    local reader_name="$2"
    local db_path="$3"
    local write_cmd="$4"

    run_test "$writer_name" "$reader_name" "$db_path" "$write_cmd" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql" "store"
    run_test "$writer_name" "$reader_name" "$db_path" "$write_cmd" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql" "update"
    run_test "$writer_name" "$reader_name" "$db_path" "$write_cmd" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql" "delete"
}

run_all_modes "Go" "Go" "$DB_GO" "$DIR/go_write_matrix"
run_all_modes "Go" "Rust" "$DB_GO" "$DIR/go_write_matrix"
run_all_modes "Go" "Python" "$DB_GO" "$DIR/go_write_matrix"
run_all_modes "Go" "Node" "$DB_GO" "$DIR/go_write_matrix"

run_all_modes "Rust" "Rust" "$DB_RUST" "$DIR/rust_write_matrix"
run_all_modes "Rust" "Go" "$DB_RUST" "$DIR/rust_write_matrix"
run_all_modes "Rust" "Python" "$DB_RUST" "$DIR/rust_write_matrix"
run_all_modes "Rust" "Node" "$DB_RUST" "$DIR/rust_write_matrix"
"""

content = content.split('# Go tests')[0] + new_test_calls + '\n# Clean up binaries\nrm -f "$DIR/go_write_matrix" "$DIR/rust_write_matrix"\n'

with open("integration-tests/write-matrix/test_writer_matrix.sh", "w") as f:
    f.write(content)
