#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$DIR")"

echo "=== Running Python Tests ==="
(cd "$ROOT_DIR/python" && python3 -m pip install -e ".[test]" && python3 -m pytest)

echo "=== Running Node.js Tests ==="
(cd "$ROOT_DIR/nodejs" && npm ci && npm test)

echo "=== Running Browser Tests ==="
(cd "$ROOT_DIR/browser-test" && npm ci && npm test)

echo "=== Running Integration Roundtrip Tests ==="
"$ROOT_DIR/integration-tests/roundtrip/test_roundtrip.sh"

if command -v zig >/dev/null 2>&1; then
  echo "=== Running Zig Smoke Tests ==="
  (cd "$ROOT_DIR/zig" && zig build run && zig build test)
else
  echo "=== Skipping Zig Smoke Tests: zig not found ==="
fi

echo "=== All Tests Completed Successfully! ==="
