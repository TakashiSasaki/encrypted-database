# Python/Node.js First Public Release Governance

## Scope
This document outlines the governance and policy decisions for the upcoming first public release of the `baseline-public` certified Python and Node.js packages.
Phase 11 prepared the release-candidate freeze. Phase 12 establishes the non-publishing publication runbook and execution readiness gate. Neither phase actually publishes artifacts, creates credentials, or pushes tags.

- **Python package scope:** Stable read/write implementation of Storage Format V1.
- **Node.js package scope:** Stable read/write implementation of Storage Format V1.
- **Storage Format V1:** Semantics remain unchanged.

## Package Names Under Consideration
- **Python:** `encrypted_storage` (Recommended)
- **Node.js:** `encrypted-storage` vs `@vault/encrypted-storage` (Pending decision)

## Versioning Policy
- **Candidate Version:** Both packages align on the initial candidate version, `0.1.0`.
- **Tag Naming Convention:** Future tags will follow standard format, e.g., `v0.1.0`.
- **Alignment:** Python and Node.js versions remain aligned to indicate feature parity.

## Manual Release Approval Gate
- **Approval:** A release manager must manually approve the final release PR.
- **Evidence Review:** The reviewer must verify the automated preflight evidence (Phase 9 matrix passes, artifact hash manifest is clean).
- **Automation:** There is no automatic publish before explicit approval. Release workflows and publication execution are future explicit work.

## Trusted Publishing & Token Policy
- **PyPI:** Trusted Publishing (OIDC) is the preferred path. Token policies will be considered if OIDC is unavailable.
- **npm:** Automation tokens or granular access tokens are preferred; manual publishing may be considered as a fallback.
- **Secrets Policy:** Credentials and tokens must **never** be committed to the repository. No accounts, trusted publishing, or tokens are currently configured.

## Release Artifact Manifest Policy
Release distributions will generate an artifact manifest (JSON) outside of the repository tracked paths, containing:
- Package name, version, and language
- Artifact filename and type
- SHA-256 hashes
- Size in bytes

## Release Notes Requirements
Release notes for the first public release candidate must include:
- A statement of `baseline-public` status for Python and Node.js.
- A statement that Storage Format V1 is Stable and unchanged.
- A clear list of supported APIs and known boundaries.
- A statement explicitly noting that this is not an external security audit.
- Clear indicators that installation commands represent future actions and not evidence of current publication.

## Rollback / Yank Policy
- **When to yank:** Only in the event of severe security vulnerabilities or broken installations that affect all users immediately upon install.
- **When not to yank:** Minor bugs or backwards-compatible feature omissions should be addressed in patch releases.
- **Compatibility:** Storage Format V1 stability guarantee remains the priority.

## Post-Release Verification (Future)
After a successful publish to PyPI and npm, post-release verification will consist of:
- Clean installation from the public registry (e.g. `pip install encrypted_storage`).
- Executing the smoke tests against the installed public artifact.
- (Optional) Running the cross-language installed-distribution matrix using the downloaded artifacts.

## Explicit Non-Goals for Phase 11
- No actual publication to PyPI/npm.
- No credentials or secrets committed to the repository.
- No Git tags created or pushed.
- No generated artifacts written to tracked repository paths.
- No changes to Storage Format V1 bytes-on-disk semantics.
