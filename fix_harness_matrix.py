with open("docs/implementation-notes/project-wide-public-library-quality-harness.md", "r") as f:
    content = f.read()

# Make sure we remove public-entrypoint public-entrypoint if it got created. Wait, `check_stale_docs.sh` checks for that but we already passed it.
# Check that the documentation states Phase 9 matrix and Phase 10 governance.

content = content.replace("Phase 10 governance and non-secret publication readiness stride is active to prepare final pre-publish documents. Phase 10 governance and non-secret publication readiness stride is active to prepare final pre-publish documents.", "Phase 10 governance and non-secret publication readiness stride is active to prepare final pre-publish documents.")

with open("docs/implementation-notes/project-wide-public-library-quality-harness.md", "w") as f:
    f.write(content)
