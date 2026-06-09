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
  echo "=== Running Zig Tests and Shared Vectors ==="
  (cd "$ROOT_DIR/zig" && zig build run && zig build test && zig build vectors)
else
  echo "=== Skipping Zig Tests and Shared Vectors: zig not found ==="
fi

echo "=== Zig selected read-only fixture decrypt is covered by integration-tests/read-only-matrix/test_readonly_matrix.sh and the Read-only Matrix workflow ==="

echo "=== All Tests Completed Successfully! ==="
