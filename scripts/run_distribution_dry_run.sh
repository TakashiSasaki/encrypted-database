#!/usr/bin/env bash
set -e

# Distribution Dry-Run Helper Script
# Runs a safe local dry-run of building and smoke testing Python and Node.js packages.
# Does NOT publish to PyPI or npm.

echo "=========================================="
echo "Starting Distribution Dry-Run"
echo "=========================================="

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

echo "[1/4] Python Build Dry-Run"
cd "$REPO_ROOT/python"
if ! python -c "import build" &> /dev/null; then
    python -m pip install build
fi
python -m build --outdir "$TEMP_DIR/python_dist"

# Find the artifacts
WHEEL_FILE=$(ls "$TEMP_DIR/python_dist"/*.whl | head -n 1)
SDIST_FILE=$(ls "$TEMP_DIR/python_dist"/*.tar.gz | head -n 1)

echo "[2/4] Python Smoke Test (Clean Install - Wheel)"
python -m venv "$TEMP_DIR/pyvenv_wheel"
source "$TEMP_DIR/pyvenv_wheel/bin/activate"
python -m pip install "$WHEEL_FILE"
echo "Running Python smoke test script (Wheel)..."
python -c "
import os
import encrypted_storage
print('SUCCESS: Python wheel package root import works.')
print(f'Version: {getattr(encrypted_storage, \"__version__\", \"<no version>\")}')

db_path = 'test_smoke_py_wheel.sqlite'
try:
    storage = encrypted_storage.EncryptedStorage(db_path)
    storage.initialize_database('test-password', 'linux')
    print('SUCCESS: Python wheel database initialization works (schema.sql bundled correctly).')
finally:
    if os.path.exists(db_path):
        os.remove(db_path)
"
deactivate

echo "[2.5/4] Python Smoke Test (Clean Install - sdist)"
python -m venv "$TEMP_DIR/pyvenv_sdist"
source "$TEMP_DIR/pyvenv_sdist/bin/activate"
python -m pip install "$SDIST_FILE"
echo "Running Python smoke test script (sdist)..."
python -c "
import os
import encrypted_storage
print('SUCCESS: Python sdist package root import works.')
print(f'Version: {getattr(encrypted_storage, \"__version__\", \"<no version>\")}')

db_path = 'test_smoke_py_sdist.sqlite'
try:
    storage = encrypted_storage.EncryptedStorage(db_path)
    storage.initialize_database('test-password', 'linux')
    print('SUCCESS: Python sdist database initialization works (schema.sql bundled correctly).')
finally:
    if os.path.exists(db_path):
        os.remove(db_path)
"
deactivate


echo "[3/4] Node.js Pack Dry-Run"
cd "$REPO_ROOT/nodejs"
npm pack --pack-destination "$TEMP_DIR"

TARBALL_FILE=$(ls "$TEMP_DIR"/encrypted-storage-*.tgz | head -n 1)

echo "[4/4] Node.js Smoke Test (Clean Install)"
mkdir -p "$TEMP_DIR/nodetest"
cd "$TEMP_DIR/nodetest"
npm init -y > /dev/null
npm install "$TARBALL_FILE" > /dev/null

node -e "
const fs = require('fs');
const pkg = require('encrypted-storage');
console.log('SUCCESS: Node.js package root require works.');
console.log('EncryptedStorage:', typeof pkg.EncryptedStorage);
console.log('StorageError:', typeof pkg.StorageError);

async function runTest() {
    const dbPath = 'test_smoke_node.sqlite';
    try {
        const storage = new pkg.EncryptedStorage(dbPath);
        await storage.initializeDatabase('test-password', 'linux');
        console.log('SUCCESS: Node.js database initialization works (schema.sql bundled correctly).');
    } finally {
        if (fs.existsSync(dbPath)) fs.unlinkSync(dbPath);
    }
}
runTest().catch(e => { console.error(e); process.exit(1); });
"

echo "=========================================="
echo "✅ Distribution Dry-Run Passed Successfully"
echo "=========================================="
