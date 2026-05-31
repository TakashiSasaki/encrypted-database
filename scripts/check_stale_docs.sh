#!/usr/bin/env bash
set -euo pipefail

# Check for Bash >= 4.0 (required for associative arrays)
if (( BASH_VERSINFO[0] < 4 )); then
  echo "ERROR: This script requires Bash version 4.0 or higher."
  echo "Current version: $BASH_VERSION"
  echo "On macOS, you can install a newer Bash via Homebrew: brew install bash"
  exit 1
fi

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$DIR")"

echo "Checking for stale documentation phrases..."

# Define an array of forbidden/stale regex patterns and their descriptions
declare -A STALE_PHRASES=(
  ["Python and Node\.js payload update/delete not implemented"]="Python/Node update/delete is fully implemented"
  ["Update/delete APIs are not implemented"]="Update/delete APIs are fully implemented"
  ["API parity is mainly blocked by update/delete"]="Core payload parity is achieved"
  ["delete NotFound behavior is only covered by Go/Rust"]="Delete behavior is tested across all readers"
  ["Go/Rust production-ready"]="Go/Rust are scaffolds, not production-ready"
  ["WAL mandatory"]="WAL is recommended, but not a strict conformance invariant"
  ["journal_mode=WAL mandatory"]="WAL is recommended, but not a strict conformance invariant"
)

# File paths to search (avoiding node_modules, build artifacts, etc.)
SEARCH_PATHS=(
  "$ROOT_DIR/docs"
  "$ROOT_DIR/go/README.md"
  "$ROOT_DIR/rust/README.md"
  "$ROOT_DIR/python/README.md"
  "$ROOT_DIR/nodejs/README.md"
  "$ROOT_DIR/browser-test/README.md"
  "$ROOT_DIR/integration-tests/write-matrix/README.md"
  "$ROOT_DIR/integration-tests/read-only-matrix/README.md"
  "$ROOT_DIR/README.md"
)

FOUND_STALE=0

for pattern in "${!STALE_PHRASES[@]}"; do
  # Run grep on the paths. -r recursive, -n line numbers, -I ignore binary, -E extended regex
  # We suppress stdout to avoid printing matches directly, but capture stderr to detect true errors.
  set +e
  output=$(grep -rnIE -- "$pattern" "${SEARCH_PATHS[@]}" 2>&1)
  exit_status=$?
  set -e

  # grep exits 0 if matched, 1 if no match, 2 if error
  if [ "$exit_status" -eq 2 ]; then
    echo "ERROR: grep failed while searching for pattern: '$pattern'"
    echo "$output"
    exit 2
  elif [ "$exit_status" -eq 0 ]; then
    echo "ERROR: Found stale phrase matching pattern: '$pattern'"
    echo "Reason: ${STALE_PHRASES[$pattern]}"
    echo "$output"
    FOUND_STALE=1
  fi
done

if [ "$FOUND_STALE" -eq 1 ]; then
  echo "Stale documentation phrases found! Please fix them."
  exit 1
else
  echo "No known stale documentation phrases found. Good job!"
  exit 0
fi
