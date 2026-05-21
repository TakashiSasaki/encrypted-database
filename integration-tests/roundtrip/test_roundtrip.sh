#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$(dirname "$DIR")")"

PASSPHRASE="roundtrip-passphrase"
DB1="$DIR/py_to_node.db"
DB2="$DIR/node_to_py.db"

# Cleanup on exit
trap 'rm -f "$DB1" "$DB2"' EXIT

FAILED=0

echo "Installing dependencies..."
cd "$ROOT_DIR/python" && pip install -e . > /dev/null 2>&1
cd "$ROOT_DIR/nodejs" && npm install > /dev/null 2>&1

echo "=== Testing Python to Node.js ==="
rm -f "$DB1"

echo "Writing in Python..."
OBJ_UUID1=$(python3 "$DIR/write_python.py" "$DB1" "$PASSPHRASE")

echo "Reading in Node.js..."
PAYLOAD1=$(node "$DIR/read_nodejs.js" "$DB1" "$PASSPHRASE" "$OBJ_UUID1")

if [[ "$PAYLOAD1" == *"PAYLOAD_MATCH_SUCCESS"* ]]; then
    echo "Python -> Node.js SUCCESS"
else
    echo "Python -> Node.js FAILED: $PAYLOAD1"
    FAILED=1
fi

echo "=== Testing Node.js to Python ==="
rm -f "$DB2"

echo "Writing in Node.js..."
OBJ_UUID2=$(node "$DIR/write_nodejs.js" "$DB2" "$PASSPHRASE")

echo "Reading in Python..."
PAYLOAD2=$(python3 "$DIR/read_python.py" "$DB2" "$PASSPHRASE" "$OBJ_UUID2")

if [[ "$PAYLOAD2" == *"PAYLOAD_MATCH_SUCCESS"* ]]; then
    echo "Node.js -> Python SUCCESS"
else
    echo "Node.js -> Python FAILED: $PAYLOAD2"
    FAILED=1
fi

if [ $FAILED -eq 0 ]; then
    echo "All roundtrip tests passed!"
else
    exit 1
fi
