#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$(dirname "$DIR")")"
DB_DIR="$DIR/tmp"

echo "Installing Python and Node.js dependencies..."
cd "$ROOT_DIR/python" && pip install -e .[test] >/dev/null
cd "$ROOT_DIR/nodejs" && npm install >/dev/null
cd "$DIR" && npm install >/dev/null

mkdir -p "$DB_DIR"

echo "=== Testing Python -> Node.js Roundtrip ==="
PYTHON_DB="$DB_DIR/python.db"
echo "Creating database with Python..."
OBJ_UUID_PY=$(python3 "$DIR/create_python_db.py" "$PYTHON_DB")
echo "Created object UUID: $OBJ_UUID_PY"

echo "Reading database with Node.js..."
if NODE_RESULT=$(node "$DIR/read_with_node.js" "$PYTHON_DB" "$OBJ_UUID_PY" 2>&1); then
    if [ "$NODE_RESULT" = "SUCCESS" ]; then
        echo "Python -> Node.js Roundtrip SUCCESS"
    else
        echo "Python -> Node.js Roundtrip FAILED"
        echo "$NODE_RESULT"
        exit 1
    fi
else
    echo "Python -> Node.js Roundtrip FAILED"
    echo "$NODE_RESULT"
    exit 1
fi

echo ""
echo "=== Testing Node.js -> Python Roundtrip ==="
NODE_DB="$DB_DIR/node.db"
echo "Creating database with Node.js..."
OBJ_UUID_NODE=$(node "$DIR/create_node_db.js" "$NODE_DB")
echo "Created object UUID: $OBJ_UUID_NODE"

echo "Reading database with Python..."
if PYTHON_RESULT=$(python3 "$DIR/read_with_python.py" "$NODE_DB" "$OBJ_UUID_NODE" 2>&1); then
    if [ "$PYTHON_RESULT" = "SUCCESS" ]; then
        echo "Node.js -> Python Roundtrip SUCCESS"
    else
        echo "Node.js -> Python Roundtrip FAILED"
        echo "$PYTHON_RESULT"
        exit 1
    fi
else
    echo "Node.js -> Python Roundtrip FAILED"
    echo "$PYTHON_RESULT"
    exit 1
fi

echo ""
echo "All roundtrip tests passed!"

# Cleanup
rm -rf "$DB_DIR"
