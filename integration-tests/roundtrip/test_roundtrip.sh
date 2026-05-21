#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$(dirname "$DIR")")"

PASSPHRASE="roundtrip-passphrase"
DB1="$DIR/py_to_node.db"
DB2="$DIR/node_to_py.db"

# Cleanup on exit (will run on success and failure)
trap 'rm -f "$DB1" "$DB2"' EXIT



echo "Installing dependencies..."
# Fail immediately if installs fail
(cd "$ROOT_DIR/python" && pip install -e . > /dev/null 2>&1)
(cd "$ROOT_DIR/nodejs" && npm install > /dev/null 2>&1)

echo "=== Testing Python to Node.js ==="
rm -f "$DB1"

echo "Writing in Python..."
# If write script fails, set -e will abort the script here
OBJ_UUID1=$(python3 "$DIR/write_python.py" "$DB1" "$PASSPHRASE")

echo "Reading in Node.js..."
# Run the reader script directly without capturing output so errors stream to stderr
# We only capture if we want to parse it, but if we capture it, set -e will abort on non-zero exit anyway.
node "$DIR/read_nodejs.js" "$DB1" "$PASSPHRASE" "$OBJ_UUID1"
echo "Python -> Node.js SUCCESS"

echo "=== Testing Node.js to Python ==="
rm -f "$DB2"

echo "Writing in Node.js..."
OBJ_UUID2=$(node "$DIR/write_nodejs.js" "$DB2" "$PASSPHRASE")

echo "Reading in Python..."
python3 "$DIR/read_python.py" "$DB2" "$PASSPHRASE" "$OBJ_UUID2"
echo "Node.js -> Python SUCCESS"

echo "All roundtrip tests passed!"
