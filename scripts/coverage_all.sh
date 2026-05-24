#!/bin/bash
set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$DIR")"

echo "=== Running Python Coverage ==="
(cd "$ROOT_DIR/python" && python3 -m pip install -e ".[test]" && python3 -m pytest --cov=src --cov-report=xml --cov-report=term)

echo "=== Running Node.js Coverage ==="
# Ensure package.json has test:coverage, otherwise fallback to standard jest
(cd "$ROOT_DIR/nodejs" && npm ci && (npm run test:coverage || npm test))

echo "=== Running Browser-test Coverage ==="
(cd "$ROOT_DIR/browser-test" && npm ci && (npm run test:coverage || npm test))

echo "=== Coverage Generation Completed! ==="
echo "Artifacts:"
echo "  - python/coverage.xml"
echo "  - nodejs/coverage/lcov.info"
echo "  - browser-test/coverage/lcov.info"
