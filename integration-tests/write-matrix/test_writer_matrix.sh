#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$(dirname "$DIR")")"

PASSPHRASE="writer-matrix-passphrase"
PLATFORM="linux"
SCHEMA_UUID="00000000-0000-4000-8000-000000000001"
CONTENT_TYPE="application/json"
PAYLOAD_JSON='{"secret": "matrix-test", "value": 42}'

DB_GO="$DIR/go_writer.db"
DB_RUST="$DIR/rust_writer.db"

# Cleanup on exit
trap 'rm -f "$DB_GO" "$DB_RUST" "$DIR/go_write_matrix" "$DIR/go_write_matrix_update" "$DIR/go_write_matrix_delete" "$DIR/rust_write_matrix" "$DIR/rust_write_matrix_update" "$DIR/rust_write_matrix_delete"' EXIT

echo "Building Go wrapper..."
(cd "$ROOT_DIR/go" && go build -o "$DIR/go_write_matrix" ./cmd/write_matrix_fixture)
(cd "$ROOT_DIR/go" && go build -o "$DIR/go_write_matrix_update" ./cmd/write_matrix_update)
(cd "$ROOT_DIR/go" && go build -o "$DIR/go_write_matrix_delete" ./cmd/write_matrix_delete)

echo "Building Rust wrapper..."
(cd "$ROOT_DIR/rust" && cargo build --bin write_matrix_fixture)
cp "$ROOT_DIR/rust/target/debug/write_matrix_fixture" "$DIR/rust_write_matrix"
(cd "$ROOT_DIR/rust" && cargo build --bin write_matrix_update)
(cd "$ROOT_DIR/rust" && cargo build --bin write_matrix_delete)
cp "$ROOT_DIR/rust/target/debug/write_matrix_update" "$DIR/rust_write_matrix_update"
cp "$ROOT_DIR/rust/target/debug/write_matrix_delete" "$DIR/rust_write_matrix_delete"

echo "Preparing Node.js environment..."
(cd "$ROOT_DIR/nodejs" && npm ci > /dev/null 2>&1)

echo "Preparing Python environment..."
(cd "$ROOT_DIR/python" && pip install -e .[test] > /dev/null 2>&1)

# Function to run the write/read test
run_test() {
    local writer_name="$1"
    local reader_name="$2"
    local db_path="$3"
    local write_cmd="$4"
    local update_cmd="$5"
    local delete_cmd="$6"
    local env_vars="$7"

    echo "=== Testing $writer_name Writer -> $reader_name Reader ==="
    rm -f "$db_path"

    echo "Writing..."
    # Set environment variables for schema path
    local output
    output=$(env $env_vars "$write_cmd" "$db_path" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_JSON")

    # Output should be two lines: obj_uuid and expected_payload_hex
    local obj_uuid=$(echo "$output" | head -n 1)
    local expected_payload_hex=$(echo "$output" | tail -n 1)

    echo "Reading..."
    if [ "$reader_name" == "Go" ]; then
        (cd "$ROOT_DIR/go" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$expected_payload_hex" go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly)
    elif [ "$reader_name" == "Rust" ]; then
        (cd "$ROOT_DIR/rust" && VAULT_SQLITE_V1_FIXTURE_DB="$db_path" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$obj_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$expected_payload_hex" cargo test --test sqlitev1_external_fixture)
    elif [ "$reader_name" == "Python" ]; then
        local py_out=$(python3 "$DIR/read_fixture_python.py" "$db_path" "$PASSPHRASE" "$obj_uuid")
        local actual_hex=$(python3 -c "import sys, json; print(json.loads(sys.stdin.read())['payload_hex'])" <<< "$py_out")
        if [ -z "$actual_hex" ] || [ "$actual_hex" != "$expected_payload_hex" ]; then
            echo "Python Reader Failed: Expected $expected_payload_hex, got $actual_hex"
            exit 1
        fi
    elif [ "$reader_name" == "Node" ]; then
        local node_out=$(node "$DIR/read_fixture_node.js" "$db_path" "$PASSPHRASE" "$obj_uuid")
        local actual_hex=$(python3 -c "import sys, json; print(json.loads(sys.stdin.read())['payload_hex'])" <<< "$node_out")
        if [ -z "$actual_hex" ] || [ "$actual_hex" != "$expected_payload_hex" ]; then
            echo "Node Reader Failed: Expected $expected_payload_hex, got $actual_hex"
            exit 1
        fi
    fi

    echo "$writer_name -> $reader_name SUCCESS"
    echo ""
}

# Go tests
run_test "Go" "Go" "$DB_GO" "$DIR/go_write_matrix" "$DIR/go_write_matrix_update" "$DIR/go_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"
run_test "Go" "Rust" "$DB_GO" "$DIR/go_write_matrix" "$DIR/go_write_matrix_update" "$DIR/go_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"
run_test "Go" "Python" "$DB_GO" "$DIR/go_write_matrix" "$DIR/go_write_matrix_update" "$DIR/go_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"
run_test "Go" "Node" "$DB_GO" "$DIR/go_write_matrix" "$DIR/go_write_matrix_update" "$DIR/go_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"

# Rust tests
run_test "Rust" "Rust" "$DB_RUST" "$DIR/rust_write_matrix" "$DIR/rust_write_matrix_update" "$DIR/rust_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"
run_test "Rust" "Go" "$DB_RUST" "$DIR/rust_write_matrix" "$DIR/rust_write_matrix_update" "$DIR/rust_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"
run_test "Rust" "Python" "$DB_RUST" "$DIR/rust_write_matrix" "$DIR/rust_write_matrix_update" "$DIR/rust_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"
run_test "Rust" "Node" "$DB_RUST" "$DIR/rust_write_matrix" "$DIR/rust_write_matrix_update" "$DIR/rust_write_matrix_delete" "VAULT_SCHEMA_SQL_PATH=$ROOT_DIR/docs/backend/sqlite/schema.sql"

# Clean up binaries
rm -f "$DIR/go_write_matrix" "$DIR/rust_write_matrix"
