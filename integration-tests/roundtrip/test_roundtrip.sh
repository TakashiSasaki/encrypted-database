#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$(dirname "$DIR")")"

PASSPHRASE="supersecretpassphrase"
FAILED=0

echo "=== Testing Python to Node.js ==="
DB1="$DIR/py_to_node.db"
rm -f "$DB1"

echo "Writing in Python..."
cd "$ROOT_DIR/python" && pip install -e . > /dev/null 2>&1
OBJ_UUID1=$(python3 "$DIR/write_python.py" "$DB1" "$PASSPHRASE")

echo "Reading in Node.js..."
cd "$ROOT_DIR/nodejs" && npm install > /dev/null 2>&1
PAYLOAD1=$(node "$DIR/read_nodejs.js" "$DB1" "$PASSPHRASE" "$OBJ_UUID1")

if [[ "$PAYLOAD1" == *"from python"* ]]; then
    echo "Python -> Node.js SUCCESS"
else
    echo "Python -> Node.js FAILED: $PAYLOAD1"
    FAILED=1
fi

echo "=== Testing Node.js to Python ==="
DB2="$DIR/node_to_py.db"
rm -f "$DB2"

echo "Writing in Node.js..."
cd "$DIR" && npm install > /dev/null 2>&1
OBJ_UUID2=$(node "$DIR/write_nodejs.js" "$DB2" "$PASSPHRASE")

echo "Reading in Python..."
PAYLOAD2=$(python3 "$DIR/read_python.py" "$DB2" "$PASSPHRASE" "$OBJ_UUID2")

if [[ "$PAYLOAD2" == *"from nodejs"* ]]; then
    echo "Node.js -> Python SUCCESS"
else
    echo "Node.js -> Python FAILED: $PAYLOAD2"
    FAILED=1
fi

if [ $FAILED -eq 0 ]; then
    echo "All roundtrip tests passed!"
fi
rm -f "$DB1" "$DB2"
if [ $FAILED -ne 0 ]; then
    exit 1
fi
