#!/bin/bash
# check_stale_docs.sh
# A lightweight guardrail script to detect known stale claims or contradictory phrases in documentation.
# This script is meant to prevent regressions where old assumptions (like "Python/Node update/delete are not implemented")
# are re-introduced into the docs.
# It exits with a non-zero status code if stale phrases are detected.

set -euo pipefail

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ROOT_DIR="$(dirname "$DIR")"

echo "Checking for stale documentation phrases in docs/..."

cd "$ROOT_DIR"

FOUND_STALE=0

check_phrase() {
    local pattern="$1"
    local desc="$2"
    local matches=$(grep -rnEi "$pattern" docs/ go/ rust/ python/ nodejs/ browser-test/ --exclude-dir="node_modules" --exclude-dir="__pycache__" --exclude-dir="target" --exclude-dir="dist" 2>/dev/null || true)
    if [ -n "$matches" ]; then
        echo "❌ Found stale phrase: $desc (pattern: '$pattern')"
        echo "$matches"
        FOUND_STALE=1
    fi
}

# 1. Claims that Python/Node update/delete are not implemented.
check_phrase "not present as public APIs in Python/Node\.js" "Stale claim about Python/Node missing update/delete public APIs"
check_phrase "Python/Node currently do not expose public update/delete" "Stale claim about Python/Node missing update/delete public APIs"

# 2. "WAL mandatory" or "journal_mode=WAL mandatory"
check_phrase "journal_mode=WAL mandatory" "Stale claim: WAL is recommended, but not a strict conformance requirement"
check_phrase "WAL mandatory" "Stale claim: WAL is recommended, but not a strict conformance requirement"

# 3. Claims that current Go/Rust code are full production libraries (they are scaffolds)
# Note: In implementation-gaps.md, the phrase "Go/Rust full production storage libraries are not yet implemented" is valid.
# So we need to look for "is a full production storage library" or "are full production storage libraries".
check_phrase "is a full production storage library" "Stale/false claim: Go/Rust are scaffolds"
check_phrase "are full production storage libraries\." "Stale/false claim: Go/Rust are scaffolds"

# 4. "manual only" for write-matrix (since it is path-filtered now)
check_phrase "write-matrix is manual only" "Stale claim: write-matrix runs in path-filtered CI"

if [ "$FOUND_STALE" -eq 1 ]; then
    echo "⚠️  Stale documentation found. Please update the affected files."
    exit 1
else
    echo "✅ No stale documentation phrases found."
    exit 0
fi
