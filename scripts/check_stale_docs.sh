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

# 5. Overstatements of test_all.sh
check_phrase "full suite of tests using .*test_all\.sh" "Stale claim: test_all.sh is a baseline aggregate, not the complete full suite"

# 6. Go/Wasm as vague idea
check_phrase "Go/Wasm .* vague future" "Stale claim: Go/Wasm is an explicit development target"
check_phrase "vague future .* Go/Wasm" "Stale claim: Go/Wasm is an explicit development target"
check_phrase "Go/Wasm .* vague idea" "Stale claim: Go/Wasm is an explicit development target"
check_phrase "vague idea .* Go/Wasm" "Stale claim: Go/Wasm is an explicit development target"

# 7. Pre-v1 "Draft" or "Candidate" terminology in docs
check_phrase "Storage Format V1 .* Draft" "Stale claim: V1 is Stable"
check_phrase "Storage Format V1 .* Candidate" "Stale claim: V1 is Stable"
check_phrase "V1 is a Draft" "Stale claim: V1 is Stable"
check_phrase "V1 is a Candidate" "Stale claim: V1 is Stable"

# 8. Claims that V1 format can be mutated ("controlled amendments")
check_phrase "controlled amendments may be considered" "Stale claim: Storage Format V1 is strictly Stable; breaking changes must be V2"
check_phrase "controlled V1 amendments may be considered" "Stale claim: Storage Format V1 is strictly Stable; breaking changes must be V2"
check_phrase "Amendment rules" "Stale claim: 'Amendment rules' implies an active policy, which is no longer true for V1"
check_phrase "Go/Rust Portability Validation Policy and Amendment rules" "Stale claim: 'Amendment rules' implies an active policy, which is no longer true for V1"

# 9. Claims that Go/Rust are only in the initial test vector discovery phase
check_phrase "current phase focuses solely on test vector discovery" "Stale claim: Go/Rust have advanced beyond test vector discovery"
check_phrase "eventually full database interaction" "Stale claim: Go/Rust have already reached database interaction"

# 10. Claims that read/write implementations don't exist at all yet
check_phrase "before full read/write implementations are developed" "Stale claim: Go/Rust now have read-only readers and writer scaffolds, even if not full production libraries"

# 11. Overclaims about full public API parity
check_phrase "all languages have full public API parity" "Stale claim: API parity is mostly limited to payload operations, not full lifecycle parity"
check_phrase "store/retrieve/update/delete parity implies full API parity" "Stale claim: payload operation parity does not imply full public API parity"

# 12. Claims about browser-test being full real-browser WebCrypto
check_phrase "browser-test provides full real-browser WebCrypto coverage" "Stale claim: browser-test is a test harness using sql.js and a Node crypto shim"
check_phrase "browser-test is full real-browser WebCrypto coverage" "Stale claim: browser-test is a test harness using sql.js and a Node crypto shim"

# 13. Claims about write-matrix coverage including Python/Node writers
check_phrase "write-matrix includes Python/Node writer outputs" "Stale claim: Python/Node writer generated databases are not yet included in the write-matrix"


# 14. Claims about Python/Node writer APIs missing vs matrix coverage
check_phrase "Python/Node writer APIs are missing" "Stale claim: Python/Node public writer APIs exist, but Python/Node writer-generated databases are not yet included in write-matrix coverage"
check_phrase "Node writer APIs are missing" "Stale claim: Node public writer APIs exist, but writer-generated databases are not yet included in write-matrix coverage"
check_phrase "Python writer APIs are missing" "Stale claim: Python public writer APIs exist, but writer-generated databases are not yet included in write-matrix coverage"

# 15. Claims that stability means whole library production-ready
check_phrase "Storage Format V1 stability means the whole library is production-ready" "Stale claim: Storage Format V1 is Stable, but whole library is not yet declared production-ready"

if [ "$FOUND_STALE" -eq 1 ]; then
    echo "⚠️  Stale documentation found. Please update the affected files."
    exit 1
else
    echo "✅ No stale documentation phrases found."
    exit 0
fi
