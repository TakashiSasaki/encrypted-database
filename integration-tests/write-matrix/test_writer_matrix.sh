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
DB_GO="$DIR/go_writer.db"; DB_RUST="$DIR/rust_writer.db"; DB_ZIG="$DIR/zig_writer.db"
trap 'rm -f "$DB_GO" "$DB_RUST" "$DB_ZIG" "$DB_GO"-wal "$DB_GO"-shm "$DB_RUST"-wal "$DB_RUST"-shm "$DB_ZIG"-wal "$DB_ZIG"-shm "$DIR/go_write_matrix" "$DIR/rust_write_matrix" "$DIR/zig_write_matrix"' EXIT

(cd "$ROOT_DIR/go" && go build -o "$DIR/go_write_matrix" ./cmd/write_matrix_fixture)
(cd "$ROOT_DIR/rust" && cargo build --bin write_matrix_fixture)
cp "$ROOT_DIR/rust/target/debug/write_matrix_fixture" "$DIR/rust_write_matrix"
(cd "$ROOT_DIR/zig" && zig build)
cp "$ROOT_DIR/zig/zig-out/bin/vault-zig-smoke-test" "$DIR/zig_write_matrix"

(cd "$ROOT_DIR/nodejs" && npm ci >/dev/null 2>&1)
(cd "$ROOT_DIR/python" && pip install -e .[test] >/dev/null 2>&1)

run_updated_payload_check() {
 local writer="$1" reader="$2" db="$3" cmd="$4"
 local cmd_arg="${5:-}"
 rm -f "$db" "$db-wal" "$db-shm"
 local out object_uuid updated_hex deleted
 if [ -n "$cmd_arg" ]; then
   out=$(VAULT_SCHEMA_SQL_PATH="$ROOT_DIR/docs/backend/sqlite/schema.sql" "$cmd" "$cmd_arg" "$db" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_A_JSON" "$PAYLOAD_B_JSON" update_only)
 else
   out=$(VAULT_SCHEMA_SQL_PATH="$ROOT_DIR/docs/backend/sqlite/schema.sql" "$cmd" "$db" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_A_JSON" "$PAYLOAD_B_JSON" update_only)
 fi
 object_uuid=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["object_uuid"])' <<<"$out")
 updated_hex=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["updated_payload_hex"])' <<<"$out")
 deleted=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["deleted"])' <<<"$out")
 [ "$deleted" = "False" ] || { echo "expected deleted=false for update_only"; return 1; }

 if [ "$reader" = "Python" ]; then
   local py_out=$(python3 "$DIR/read_fixture_python.py" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["payload_hex"])' <<<"$py_out")" = "$updated_hex" ] || return 1
 elif [ "$reader" = "Node" ]; then
   local no=$(node "$DIR/read_fixture_node.js" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["payload_hex"])' <<<"$no")" = "$updated_hex" ] || return 1
 elif [ "$reader" = "Go" ]; then
   (cd "$ROOT_DIR/go" && VAULT_SQLITE_V1_FIXTURE_DB="$db" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$object_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$updated_hex" go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly)
 elif [ "$reader" = "Rust" ]; then
   (cd "$ROOT_DIR/rust" && VAULT_SQLITE_V1_FIXTURE_DB="$db" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$object_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="$updated_hex" cargo test --test sqlitev1_external_fixture)
 elif [ "$reader" = "Zig" ]; then
   local zig_out
   zig_out=$("$DIR/zig_write_matrix" read-fixture "$db" "$PASSPHRASE" "$object_uuid" "$updated_hex")
   [[ "$zig_out" == *"Read fixture successful."* ]] || return 1
 fi
 echo "$writer -> $reader updated-payload SUCCESS"
}

run_delete_notfound_check() {
 local writer="$1" reader="$2" db="$3" cmd="$4"
 local cmd_arg="${5:-}"
 rm -f "$db" "$db-wal" "$db-shm"
 local out object_uuid deleted
 if [ -n "$cmd_arg" ]; then
   out=$(VAULT_SCHEMA_SQL_PATH="$ROOT_DIR/docs/backend/sqlite/schema.sql" "$cmd" "$cmd_arg" "$db" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_A_JSON" "$PAYLOAD_B_JSON" update_delete)
 else
   out=$(VAULT_SCHEMA_SQL_PATH="$ROOT_DIR/docs/backend/sqlite/schema.sql" "$cmd" "$db" "$PASSPHRASE" "$PLATFORM" "$SCHEMA_UUID" "$CONTENT_TYPE" "$PAYLOAD_A_JSON" "$PAYLOAD_B_JSON" update_delete)
 fi
 object_uuid=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["object_uuid"])' <<<"$out")
 deleted=$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["deleted"])' <<<"$out")
 [ "$deleted" = "True" ] || { echo "expected deleted=true for update_delete"; return 1; }

 if [ "$reader" = "Go" ]; then
   (cd "$ROOT_DIR/go" && VAULT_SQLITE_V1_FIXTURE_DB="$db" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$object_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECT_NOT_FOUND=1 go test ./internal/sqlitev1 -run TestExternalFixtureReadOnly)
 elif [ "$reader" = "Rust" ]; then
   (cd "$ROOT_DIR/rust" && VAULT_SQLITE_V1_FIXTURE_DB="$db" VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="$PASSPHRASE" VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="$object_uuid" VAULT_SQLITE_V1_FIXTURE_EXPECT_NOT_FOUND=1 cargo test --test sqlitev1_external_fixture)
 elif [ "$reader" = "Python" ]; then
   local py_out=$(python3 "$DIR/read_fixture_python.py" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["not_found"])' <<<"$py_out")" = "True" ] || return 1
 elif [ "$reader" = "Node" ]; then
   local no=$(node "$DIR/read_fixture_node.js" "$db" "$PASSPHRASE" "$object_uuid")
   [ "$(python3 -c 'import sys,json;print(json.loads(sys.stdin.read())["not_found"])' <<<"$no")" = "True" ] || return 1
 elif [ "$reader" = "Zig" ]; then
   set +e
   local zig_out
   zig_out=$("$DIR/zig_write_matrix" read "$db" "$PASSPHRASE" "$object_uuid" 2>&1)
   local exit_code=$?
   set -e
   [[ "$zig_out" == *"Object not found"* ]] || return 1
   [ $exit_code -ne 0 ] || return 1
 fi
 echo "$writer -> $reader delete-notfound SUCCESS"
}

# updated payload checks (all readers)
run_updated_payload_check Go Go "$DB_GO" "$DIR/go_write_matrix"
run_updated_payload_check Go Rust "$DB_GO" "$DIR/go_write_matrix"
run_updated_payload_check Go Python "$DB_GO" "$DIR/go_write_matrix"
run_updated_payload_check Go Node "$DB_GO" "$DIR/go_write_matrix"
run_updated_payload_check Rust Rust "$DB_RUST" "$DIR/rust_write_matrix"
run_updated_payload_check Rust Go "$DB_RUST" "$DIR/rust_write_matrix"
run_updated_payload_check Rust Python "$DB_RUST" "$DIR/rust_write_matrix"
run_updated_payload_check Rust Node "$DB_RUST" "$DIR/rust_write_matrix"
run_updated_payload_check Zig Go "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_updated_payload_check Zig Rust "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_updated_payload_check Zig Python "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_updated_payload_check Zig Node "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_updated_payload_check Zig Zig "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"

# delete-notfound checks (all readers)
run_delete_notfound_check Go Go "$DB_GO" "$DIR/go_write_matrix"
run_delete_notfound_check Go Rust "$DB_GO" "$DIR/go_write_matrix"
run_delete_notfound_check Go Python "$DB_GO" "$DIR/go_write_matrix"
run_delete_notfound_check Go Node "$DB_GO" "$DIR/go_write_matrix"
run_delete_notfound_check Rust Go "$DB_RUST" "$DIR/rust_write_matrix"
run_delete_notfound_check Rust Rust "$DB_RUST" "$DIR/rust_write_matrix"
run_delete_notfound_check Rust Python "$DB_RUST" "$DIR/rust_write_matrix"
run_delete_notfound_check Rust Node "$DB_RUST" "$DIR/rust_write_matrix"
run_delete_notfound_check Zig Go "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_delete_notfound_check Zig Rust "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_delete_notfound_check Zig Python "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_delete_notfound_check Zig Node "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
run_delete_notfound_check Zig Zig "$DB_ZIG" "$DIR/zig_write_matrix" "write-matrix"
