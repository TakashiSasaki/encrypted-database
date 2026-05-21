#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
DB_DIR="$DIR/tmp"

mkdir -p "$DB_DIR"

echo "=== Testing Python -> Node.js Roundtrip ==="
PYTHON_DB="$DB_DIR/python.db"
echo "Creating database with Python..."
OBJ_UUID_PY=$(python3 "$DIR/create_python_db.py" "$PYTHON_DB")
echo "Created object UUID: $OBJ_UUID_PY"

echo "Reading database with Node.js..."
NODE_RESULT=$(node "$DIR/read_with_node.js" "$PYTHON_DB" "$OBJ_UUID_PY")
if [ "$NODE_RESULT" = "SUCCESS" ]; then
    echo "Python -> Node.js Roundtrip SUCCESS"
else
    echo "Python -> Node.js Roundtrip FAILED"
    echo "$NODE_RESULT"
    # exit 1 will be triggered by set -e if we failed above anyway, but we just print here
fi

echo ""
echo "=== Testing Node.js -> Python Roundtrip ==="
NODE_DB="$DB_DIR/node.db"
echo "Creating database with Node.js..."
OBJ_UUID_NODE=$(node "$DIR/create_node_db.js" "$NODE_DB")
echo "Created object UUID: $OBJ_UUID_NODE"

echo "Reading database with Python..."
PYTHON_RESULT=$(python3 "$DIR/read_with_python.py" "$NODE_DB" "$OBJ_UUID_NODE")
if [ "$PYTHON_RESULT" = "SUCCESS" ]; then
    echo "Node.js -> Python Roundtrip SUCCESS"
else
    echo "Node.js -> Python Roundtrip FAILED"
    echo "$PYTHON_RESULT"
fi

echo ""
echo "All roundtrip tests passed!"

# Cleanup
rm -rf "$DB_DIR"
