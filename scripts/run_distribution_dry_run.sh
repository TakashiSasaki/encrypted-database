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

# Find the wheel
WHEEL_FILE=$(ls "$TEMP_DIR/python_dist"/*.whl | head -n 1)

echo "[2/4] Python Smoke Test (Clean Install)"
python -m venv "$TEMP_DIR/pyvenv"
source "$TEMP_DIR/pyvenv/bin/activate"
python -m pip install "$WHEEL_FILE"
echo "Running Python smoke test script..."
python -c "
import encrypted_storage
print('SUCCESS: Python package root import works.')
print(f'EncryptedStorage: {encrypted_storage.EncryptedStorage}')
print(f'StorageError: {encrypted_storage.StorageError}')
print(f'Version: {getattr(encrypted_storage, \"__version__\", \"<no version>\")}')
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
const pkg = require('encrypted-storage');
console.log('SUCCESS: Node.js package root require works.');
console.log('EncryptedStorage:', typeof pkg.EncryptedStorage);
console.log('StorageError:', typeof pkg.StorageError);
"

echo "=========================================="
echo "✅ Distribution Dry-Run Passed Successfully"
echo "=========================================="
