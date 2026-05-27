#!/bin/bash
set -euo pipefail
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$(dirname "$DIR")")"
PASSPHRASE="writer-matrix-passphrase"
PLATFORM="linux"
SCHEMA_UUID="00000000-0000-4000-8000-000000000001"
CONTENT_TYPE="application/json"
PAYLOAD_A_JSON='{"secret":"matrix-test","value":42}'
PAYLOAD_B_JSON='{"secret":"matrix-test-updated","value":99}'
DB_GO="$DIR/go_writer.db"; DB_RUST="$DIR/rust_writer.db"
trap 'rm -f "$DB_GO" "$DB_RUST" "$DB_GO"-wal "$DB_GO"-shm "$DB_RUST"-wal "$DB_RUST"-shm "$DIR/go_write_matrix" "$DIR/rust_write_matrix"' EXIT

(cd "$ROOT_DIR/go" && go build -o "$DIR/go_write_matrix" ./cmd/write_matrix_fixture)
(cd "$ROOT_DIR/rust" && cargo build --bin write_matrix_fixture)
cp "$ROOT_DIR/rust/target/debug/write_matrix_fixture" "$DIR/rust_write_matrix"
(cd "$ROOT_DIR/nodejs" && npm ci >/dev/null 2>&1)
(cd "$ROOT_DIR/python" && pip install -e .[test] >/dev/null 2>&1)

run_test() {
 local writer="$1" reader="$2" db="$3" cmd="$4"
 rm -f "$db" "$db-wal" "$db-shm"
 local out=$(VAULT_SCHEMA_SQL_PATH="$ROOT_DIR/docs/backend/sqlite/schema.sql" "$cmd" "$db" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_A_JSON" "$PAYLOAD_B_JSON")
 local object_uuid initial_hex updated_hex deleted
 object_uuid=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["object_uuid"])' <<<"$out")
 initial_hex=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["initial_payload_hex"])' <<<"$out")
 updated_hex=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["updated_payload_hex"])' <<<"$out")
 deleted=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["deleted"])' <<<"$out")
 [ "$deleted" = "True" ] || { echo "delete flag false"; exit 1; }

 # initial read
 if [ "$reader" = "Python" ]; then
   local py_out=$(python3 "$DIR/read_fixture_python.py" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["payload_hex"])' <<<"$py_out")" = "$updated_hex" ] || exit 1
 elif [ "$reader" = "Node" ]; then
   local no=$(node "$DIR/read_fixture_node.js" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["payload_hex"])' <<<"$no")" = "$updated_hex" ] || exit 1
 elif [ "$reader" = "Go" ]; then
   (cd "$ROOT_DIR/go" && VAULT_SQLITE_V1_FIXTURE_DB="$db" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$object_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$updated_hex" go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly)
 elif [ "$reader" = "Rust" ]; then
   (cd "$ROOT_DIR/rust" && VAULT_SQLITE_V1_FIXTURE_DB="$db" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$object_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$updated_hex" cargo test --test sqlitev1_external_fixture)
 fi
 # delete notfound check only go/rust readers
 if [ "$reader" = "Go" ] || [ "$reader" = "Rust" ]; then
   (cd "$ROOT_DIR/$([ "$reader" = "Go" ] && echo go || echo rust)" && VAULT_SQLITE_V1_FIXTURE_DB="$db" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$object_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECT_NOT_FOUND=1 $([ "$reader" = "Go" ] && echo 'go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly' || echo 'cargo test --test sqlitev1_external_fixture'))
 fi
 echo "$writer -> $reader SUCCESS"
}
run_test Go Go "$DB_GO" "$DIR/go_write_matrix"
run_test Go Rust "$DB_GO" "$DIR/go_write_matrix"
run_test Go Python "$DB_GO" "$DIR/go_write_matrix"
run_test Go Node "$DB_GO" "$DIR/go_write_matrix"
run_test Rust Rust "$DB_RUST" "$DIR/rust_write_matrix"
run_test Rust Go "$DB_RUST" "$DIR/rust_write_matrix"
run_test Rust Python "$DB_RUST" "$DIR/rust_write_matrix"
run_test Rust Node "$DB_RUST" "$DIR/rust_write_matrix"
