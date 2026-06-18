import os
import re
import sys

def check_file_exists(path):
    if not os.path.exists(path):
        print(f"❌ Error: Required file missing: {path}")
        return False
    return True

def check_content(path, require_patterns, forbid_patterns):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    success = True
    for pattern in require_patterns:
        if not re.search(pattern, content):
            print(f"❌ Error in {path}: Required pattern '{pattern}' not found.")
            success = False

    for pattern in forbid_patterns:
        if re.search(pattern, content):
            print(f"❌ Error in {path}: Forbidden pattern '{pattern}' found.")
            success = False

    return success

def main():
    print("Running lightweight baseline-public readiness docs check...")
    success = True

    audit_doc = "docs/implementation-notes/python-node-baseline-public-api-error-semantics-audit.md"
    gap_doc = "docs/implementation-notes/baseline-public-readiness-gap-analysis.md"

    if not check_file_exists(audit_doc):
        success = False

    if not check_file_exists(gap_doc):
        success = False

    if success:
        # Check gap analysis
        if not check_content(gap_doc,
            require_patterns=[
                r"python-node-baseline-public-api-error-semantics-audit.md",
                r"Python and Node.js have met all requirements and are officially \*\*certified\*\* as `baseline-public`"
            ],
            forbid_patterns=[
                r"not release certification",
                r"implemented-public\*",
                r"test-wrapper-passed means public-quality"
            ]
        ):
            success = False

        # Check audit doc
        if not check_content(audit_doc,
            require_patterns=[
                r"API Parity Status",
                r"Error Semantics Audit",
                r"json-canonicalize" # Ensure we corrected the custom implementation note
            ],
            forbid_patterns=[
                r"baseline-public certification complete",
                r"Node\.js uses a custom JCS implementation"
            ]
        ):
            success = False

    if success:
        print("✅ Baseline-public readiness docs check passed.")
        sys.exit(0)
    else:
        print("❌ Baseline-public readiness docs check failed.")
        sys.exit(1)

if __name__ == '__main__':
    main()
