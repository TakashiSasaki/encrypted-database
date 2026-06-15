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
    local matches=$(grep -rnEi "$pattern" docs/ c/ cpp/ go/ rust/ python/ nodejs/ browser-test/ --exclude-dir="node_modules" --exclude-dir="__pycache__" --exclude-dir="target" --exclude-dir="dist" --exclude-dir="build" 2>/dev/null || true)
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
check_phrase "Python/Node writer generated databases are not yet included in the write-matrix" "Stale claim: Python/Node writer generated databases are now included in the write-matrix"
check_phrase "Python/Node writer-generated databases are not yet included in write-matrix coverage" "Stale claim: Python/Node writer generated databases are now included in the write-matrix"
check_phrase "Python writer outputs are not included in the write-matrix" "Stale claim: Python writer generated databases are now included in the write-matrix"
check_phrase "Node writer outputs are not included in the write-matrix" "Stale claim: Node writer generated databases are now included in the write-matrix"

# 14. Claims about Python/Node writer APIs missing vs matrix coverage
check_phrase "Python/Node writer APIs are missing" "Stale claim: Python/Node public writer APIs exist, and writer-generated databases are included in write-matrix coverage"
check_phrase "Node writer APIs are missing" "Stale claim: Node public writer APIs exist, and writer-generated databases are included in write-matrix coverage"
check_phrase "Python writer APIs are missing" "Stale claim: Python public writer APIs exist, and writer-generated databases are included in write-matrix coverage"

# 15. Claims that stability means whole library production-ready
check_phrase "Storage Format V1 stability means the whole library is production-ready" "Stale claim: Storage Format V1 is Stable, but whole library is not yet declared production-ready"

# 16. Claims that Zig is a full implementation
check_phrase "Zig is a Storage Format V1 implementation" "Stale claim: Zig is currently just a smoke test component"
check_phrase "Zig is a full production storage library" "Stale claim: Zig is currently just a smoke test component"

# 17. Stale claims about C/C++ architecture (excluding the decision doc itself)
check_phrase_file() {
    local pattern="$1"
    local desc="$2"
    local file="$3"
    local matches=$(grep -nEi "$pattern" "$file" 2>/dev/null || true)
    if [ -n "$matches" ]; then
        echo "❌ Found stale phrase in $file: $desc (pattern: '$pattern')"
        echo "$matches"
        FOUND_STALE=1
    fi
}

check_phrase_file "needs-decision" "Stale claim: C/C++ architecture is now decided" "cpp/README.md"
check_phrase_file "whether this C\+\+ implementation will eventually wrap a common C core" "Stale claim: C/C++ are independent" "cpp/README.md"
check_phrase_file "It remains needs-decision whether C\+\+ will wrap a shared C core or be fully independent" "Stale claim: C/C++ are independent" "docs/spec/storage-format-v1-portability.md"
check_phrase_file "C\+\+ architecture relative to C remains \`needs-decision\`" "Stale claim: C/C++ are independent" "docs/implementation-notes/api-parity-matrix.md"
check_phrase_file "whether C is the low-level core and C\+\+ wraps it" "Stale claim: C/C++ are independent" "docs/implementation-notes/implementation-gaps.md"
check_phrase_file "Architecture relative to C is \`needs-decision\`" "Stale claim: C/C++ are independent" "AGENTS.md"

# 18. Narrow guards against C/C++ generic JCS false claims
check_phrase "C/C\+\+ implement full generic JCS" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ implements full generic JCS" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ provide a public JCS API" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ provides a public JCS API" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ JCS is production-ready" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ JCS implementation is production-ready" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ have full RFC 8785 coverage" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ has full RFC 8785 coverage" "Stale/false claim: C/C++ generic JCS is future"

# 19. Narrow guards against C/C++ parser/dependency false claims
check_phrase "C/C\+\+ JCS parser/dependency decision is decided" "Stale/false claim: The document is currently Proposed"
check_phrase "C/C\+\+ JCS parser and dependency decision is decided" "Stale/false claim: The document is currently Proposed"
check_phrase "C/C\+\+ raw JSON parser decision is complete" "Stale/false claim: The document is currently Proposed"
check_phrase "C/C\+\+ JCS dependency choice is complete" "Stale/false claim: The document is currently Proposed"

# 20. Narrow guards against C/C++ internal value model false claims
check_phrase "C/C\+\+ internal value model is implemented" "Stale/false claim: The internal value model is proposed, not implemented"
check_phrase "C/C\+\+ JCS internal value model is implemented" "Stale/false claim: The internal value model is proposed, not implemented"
check_phrase "C/C\+\+ generic serializer is implemented" "Stale/false claim: The generic serializer is not yet implemented"
check_phrase "C/C\+\+ JCS generic serializer is implemented" "Stale/false claim: The generic serializer is not yet implemented"
check_phrase "C/C\+\+ parser-free generic serializer is implemented" "Stale/false claim: The generic serializer is not yet implemented"
check_phrase "C/C\+\+ expose a public JCS API" "Stale/false claim: C/C++ do not expose a public JCS API"
check_phrase "C/C\+\+ support embedded NUL in JCS strings" "Stale/false claim: Embedded NUL support remains needs-decision"
check_phrase "C/C\+\+ support \\\u0000 in JCS strings" "Stale/false claim: Embedded NUL support remains needs-decision"

# 21. New guards added for matrix scope and public library status
check_phrase "all languages are production-ready" "Stale/false claim: Not all languages are production-ready"
check_phrase "C/C\\+\\+ are production storage libraries" "Stale/false claim: C/C++ are bootstrap scaffolds"
check_phrase "Go/Rust/Zig are baseline-public" "Stale/false claim: Go/Rust/Zig are portability validation scaffolds"
check_phrase "cross-language matrix passes for all languages" "Stale/false claim: Matrix only passes for baseline implementations"
check_phrase "all language implementations have full public API parity" "Stale/false claim: API parity only applies to baseline implementations"

# 22. Specific bounds for Python/Node.js and wrappers
check_phrase "baseline-public certification complete" "Stale/false claim: baseline-public certification is pending"
check_phrase "C/C\\+\\+ storage library" "Stale/false claim: C/C++ are bootstrap scaffolds, not storage libraries"
check_phrase "Python and Node.js are baseline-public" "Stale/false claim: Python and Node.js are baseline-candidates"
check_phrase "test-wrapper passed means public-quality" "Stale/false claim: test-wrapper success is evidence, not certification"
check_phrase "C/C\\+\\+ is a production storage library" "Stale/false claim: C/C++ are bootstrap scaffolds, not storage libraries"

# 23. Python/Node.js JCS Implementation Guardrails
check_phrase "Node.js uses a custom JCS implementation" "Stale/false claim: Node.js uses json-canonicalize package"
check_phrase "Python/Node.js have full JCS conformance" "Stale/false claim: Python/Node.js JCS conformance is partial, pending full shared vector coverage"
check_phrase "JCS conformance is complete" "Stale/false claim: JCS conformance is not yet complete"
check_phrase "generic-positive-coverage is not used by Python/Node.js" "Stale/false claim: generic-positive-coverage is now explicitly consumed by Python and Node.js"

# 24. Narrow guards against C/C++ crypto and SQLite false claims
check_phrase "^C/C\+\+ implement Storage Format V1 cryptography" "Stale/false claim: C/C++ cryptography is future"
check_phrase "^C/C\+\+ implements Storage Format V1 cryptography" "Stale/false claim: C/C++ cryptography is future"
check_phrase "^C/C\+\+ implement SQLite" "Stale/false claim: C/C++ SQLite is future"
check_phrase "^C/C\+\+ implements SQLite" "Stale/false claim: C/C++ SQLite is future"
check_phrase "C\+\+ wraps C as the current architecture" "Stale/false claim: C/C++ are independent"
check_phrase "C\+\+ is currently a wrapper around C" "Stale/false claim: C/C++ are independent"

# 25. Requested additional missing guardrails
check_phrase "C/C\+\+ are full production storage libraries" "Stale/false claim: C/C++ are bootstrap scaffolds"
check_phrase "C/C\+\+ is a full production storage library" "Stale/false claim: C/C++ are bootstrap scaffolds"
check_phrase "C/C\+\+ have full generic JCS conformance" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ has full generic JCS conformance" "Stale/false claim: C/C++ generic JCS is future"
check_phrase "C/C\+\+ have full public API parity" "Stale/false claim: C/C++ public API is future"

# 26. Package Metadata Guardrails
check_phrase "Homepage = \"https://github.com/example/encrypted-storage\"" "Stale claim: Homepage placeholder should be the actual repository URL"
check_phrase "\"url\": \"TBD\"" "Stale claim: Node.js repository URL placeholder should be the actual repository URL"

# 27. Narrow guards for public-entrypoint evidence
check_phrase "public-entrypoint-test-wrapper evidence means baseline-public certification" "Stale claim: public-entrypoint-test-wrapper evidence is still test-wrapper evidence, not certification"
check_phrase "public-entrypoint-test-wrapper evidence is equivalent to baseline-public certification" "Stale claim: public-entrypoint-test-wrapper evidence is still test-wrapper evidence, not certification"
check_phrase "test wrappers are no longer used" "Stale claim: test wrappers remain part of the evidence path via public entrypoints"
check_phrase "Python and Node.js are already baseline-public" "Stale claim: Python and Node.js are baseline candidates, not yet baseline-public"

# 28. Narrow guards against false baseline-public certification claims
check_phrase "Python and Node.js are baseline-public" "False certification claim: Python and Node.js are baseline candidates, not yet baseline-public"
check_phrase "public-entrypoint-test-wrapper is baseline-public" "False certification claim: public-entrypoint test-wrapper is not baseline-public"
check_phrase "public-entrypoint-test-wrapper means production-ready" "False certification claim: public-entrypoint test-wrapper is not production-ready"
check_phrase "Python/Node.js baseline-public release is complete" "False certification claim: Python/Node.js baseline-public release is not complete"
check_phrase "public_quality_certification: true" "Stale public-quality claim: public_quality_certification is still false"

# 29. Guard against stale successful status wording
check_phrase_file "test-wrapper-passed" "Stale successful status wording: use public-entrypoint-passed instead" "docs/implementation-notes/project-wide-public-library-quality-harness.md"
check_phrase_file "test-wrapper-passed" "Stale successful status wording: use public-entrypoint-passed instead" "docs/implementation-notes/baseline-public-readiness-gap-analysis.md"
check_phrase_file "test-wrapper-passed" "Stale successful status wording: use public-entrypoint-passed instead" "docs/implementation-notes/cross-language-read-write-compatibility-plan.md"
check_phrase_file "test-wrapper-passed" "Stale successful status wording: use public-entrypoint-passed instead" "README.md"

# 30. Guard against duplicate terminology
check_phrase_file "public-entrypoint public-entrypoint" "Stale duplicate wording: use public-entrypoint instead" "docs/implementation-notes/project-wide-public-library-quality-harness.md"
check_phrase_file "public-entrypoint public-entrypoint" "Stale duplicate wording: use public-entrypoint instead" "docs/implementation-notes/baseline-public-readiness-gap-analysis.md"
check_phrase_file "public-entrypoint public-entrypoint" "Stale duplicate wording: use public-entrypoint instead" "docs/implementation-notes/cross-language-read-write-compatibility-plan.md"


# 31. Guard against direct-public-api false claims
check_phrase "direct-public-api evidence means baseline-public" "Stale/false claim: direct-public-api evidence does not automatically mean baseline-public certification"
check_phrase "direct-public-api-passed means public-quality certification" "Stale/false claim: direct-public-api-passed does not automatically mean public-quality certification"
check_phrase "Python and Node.js are baseline-public" "Stale/false claim: Python and Node.js are baseline candidates, not yet baseline-public"
check_phrase "only wrapper evidence exists" "Stale claim: direct-public-api evidence now exists"
check_phrase "Full shared UUID vector integration (completed)" "Stale claim: Completed items should not be listed under remaining blockers"

# 32. Guard against stale runner default claims
check_phrase "\-\-execute defaults to \-\-mode public\-entrypoint\-wrapper" "Stale claim: --execute now defaults to direct-public-api"

# 33. Guard against Phase 6 staleness and false certifications
check_phrase "public_quality_certification: true" "False certification claim: public_quality_certification remains false until final PR"
check_phrase "remaining JCS conformance coverage" "Vague blocker phrase: Use explicit vector names or document deferrals"
check_phrase "CI evidence: Achieved" "Stale claim: CI evidence must remain accurately classified as historical or separated from local evidence"

# END OF NEW RULES

if [ "$FOUND_STALE" -eq 1 ]; then
    echo "⚠️  Stale documentation found. Please update the affected files."
    exit 1
else
    echo "✅ No stale documentation phrases found."
    exit 0
fi