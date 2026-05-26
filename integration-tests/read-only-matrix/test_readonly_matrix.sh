#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$(dirname "$DIR")")"

echo "=== Setting up environments ==="
(cd "$ROOT_DIR/python" && pip install -e .[test] > /dev/null)
(cd "$ROOT_DIR/nodejs" && npm ci > /dev/null)

TMP_DIR="$(mktemp -d)"
# Cleanup on exit
trap 'rm -rf "$TMP_DIR"' EXIT

echo ""
echo "=== Testing Python-generated DB against Go/Rust readers ==="
PY_DB="$TMP_DIR/py_fixture.db"
PY_ENV="$TMP_DIR/py_fixture.env"

# Generate Python fixture
python3 "$DIR/generate_fixture_python.py" "$PY_DB" "$PY_ENV"
if [ ! -f "$PY_ENV" ]; then
  echo "Error: Python generator failed to create environment file."
  exit 1
fi
source "$PY_ENV"

# Validate required variables exist
if [ -z "${VAULT_SQLITE_V1_FIXTURE_DB:-}" ] || \
   [ -z "${VAULT_SQLITE_V1_FIXTURE_PASSPHRASE:-}" ] || \
   [ -z "${VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID:-}" ] || \
   [ -z "${VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX:-}" ]; then
  echo "Error: Missing one or more VAULT_SQLITE_V1_FIXTURE_* environment variables in Python env file."
  exit 1
fi

if [ ! -f "${VAULT_SQLITE_V1_FIXTURE_DB:-}" ]; then
  echo "Error: Generated Python fixture DB file does not exist at ${VAULT_SQLITE_V1_FIXTURE_DB:-}"
  exit 1
fi

echo "[Go] Testing against Python fixture..."
export VAULT_SQLITE_V1_FIXTURE_DB
export VAULT_SQLITE_V1_FIXTURE_PASSPHRASE
export VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID
export VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX
(cd "$ROOT_DIR/go" && go test ./internal/sqlitev1 -run ExternalFixture -v -count=1)

echo "[Rust] Testing against Python fixture..."
(cd "$ROOT_DIR/rust" && cargo test --test sqlitev1_external_fixture)

echo ""
echo "=== Testing Node.js-generated DB against Go/Rust readers ==="
NODE_DB="$TMP_DIR/node_fixture.db"
NODE_ENV="$TMP_DIR/node_fixture.env"

# Generate Node.js fixture
node "$DIR/generate_fixture_node.js" "$NODE_DB" "$NODE_ENV"
if [ ! -f "$NODE_ENV" ]; then
  echo "Error: Node.js generator failed to create environment file."
  exit 1
fi
source "$NODE_ENV"

# Validate required variables exist
if [ -z "${VAULT_SQLITE_V1_FIXTURE_DB:-}" ] || \
   [ -z "${VAULT_SQLITE_V1_FIXTURE_PASSPHRASE:-}" ] || \
   [ -z "${VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID:-}" ] || \
   [ -z "${VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX:-}" ]; then
  echo "Error: Missing one or more VAULT_SQLITE_V1_FIXTURE_* environment variables in Node.js env file."
  exit 1
fi

if [ ! -f "${VAULT_SQLITE_V1_FIXTURE_DB:-}" ]; then
  echo "Error: Generated Node.js fixture DB file does not exist at ${VAULT_SQLITE_V1_FIXTURE_DB:-}"
  exit 1
fi

echo "[Go] Testing against Node.js fixture..."
export VAULT_SQLITE_V1_FIXTURE_DB
export VAULT_SQLITE_V1_FIXTURE_PASSPHRASE
export VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID
export VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX
(cd "$ROOT_DIR/go" && go test ./internal/sqlitev1 -run ExternalFixture -v -count=1)

echo "[Rust] Testing against Node.js fixture..."
(cd "$ROOT_DIR/rust" && cargo test --test sqlitev1_external_fixture)

echo ""
echo "All read-only matrix tests passed successfully!"
