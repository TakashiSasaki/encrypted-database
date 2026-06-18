# Python/Node.js First Public Release Human Approval Packet

**Note: This is a draft template. Approval has NOT been granted.**

This packet gathers the necessary information for a human approver to make an explicit decision to publish the `baseline-public` Python and Node.js packages to the public registries (PyPI and npm).

## Candidate Summary
- **Candidate Version:** `0.1.0`
- **Candidate Commit SHA:** `[PLACEHOLDER_COMMIT_SHA]`
- **Python Package Name Proposal:** `encrypted_storage`
- **Node.js Package Name Proposal:** `encrypted-storage`
- **npm Scoped Alternative:** `@vault/encrypted-storage` (if still considered)
- **PyPI Account/Project Owner:** `[PLACEHOLDER_PYPI_ACCOUNT]`
- **npm Account/Scope Owner:** `[PLACEHOLDER_NPM_ACCOUNT]`
- **Trusted Publishing/Token Decision:** `[PLACEHOLDER_TRUSTED_PUBLISHING]`
- **Release Manager Approval:** `[PLACEHOLDER_APPROVER_NAME]`
- **Expected Artifact Manifest Location:** `[PLACEHOLDER_MANIFEST_LOCATION_OUTSIDE_REPO]`

## Required Automation Gates
The following gates **must pass** locally before this packet can be considered actionable and publication can be performed:
1.  **Dry Run Aggregator:** `scripts/run_python_node_first_public_release_dry_run.py --require-publication-ready --include-installed-matrix --allow-network-probes --json` must return success, meaning all internal gates (preflight, release candidate gate, and publication readiness gate) pass and all decision placeholders are resolved.

## Explicit Non-Goals
This release is strictly scoped. It explicitly does **not** include or claim:
-   Promotion or public release of C, C++, Go, Rust, Zig, or browser-test implementations. They remain scaffolds.
-   Any change to the Storage Format V1 bytes-on-disk semantics.
-   Any claim of an external security audit.
-   Commitment of any real publishing credentials or tokens to the repository.

## Final Human Decisions Required
Before actual publication, the release manager must:
1.  Replace all `[PLACEHOLDER]` tags in the decision record with actual decisions or identities.
2.  Change the status in the decision record to `APPROVED` and set `Publication Authorized: true`.
3.  Ensure accounts on PyPI and npm are prepared and trusted publishing (or tokens) are securely accessible to the execution environment.
4.  Proceed with the explicit commands in the execution runbook.
