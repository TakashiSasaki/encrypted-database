# Python/Node.js First Public Release Governance

## Scope
This document outlines the governance and policy decisions for the upcoming first public release of the `baseline-public` certified Python and Node.js packages.
This stride (Phase 10) prepares for publication but does **not** actually publish any artifacts or commit any secrets.

- **Python package scope:** Stable read/write implementation of Storage Format V1.
- **Node.js package scope:** Stable read/write implementation of Storage Format V1.
- **Storage Format V1:** Semantics remain unchanged.

## Package Names Under Consideration
- **Python:** `encrypted_storage` (Recommended)
- **Node.js:** `encrypted-storage` vs `@vault/encrypted-storage` (Pending decision)

## Versioning Policy
- **Candidate Version:** Both packages will align on the initial public version, e.g., `0.1.0`.
- **Tag Naming Convention:** Tags will follow standard format, e.g., `v0.1.0`.
- **Alignment:** Python and Node.js versions remain aligned to indicate feature parity.

## Manual Release Approval Gate
- **Approval:** A release manager must manually approve the release PR.
- **Evidence Review:** The reviewer must verify the automated preflight evidence (Phase 9 matrix passes, artifact hash manifest is clean).
- **Automation:** There is no automatic publish before explicit approval. Release workflows will be manually triggered.

## Trusted Publishing & Token Policy
- **PyPI:** Trusted Publishing (OIDC) is preferred over long-lived tokens if supported by the organization.
- **npm:** Automation tokens or granular access tokens are preferred; manual publishing may be considered for the first release if token scaffolding is complex.
- **Secrets Policy:** Credentials and tokens must **never** be committed to the repository.

## Release Artifact Manifest Policy
Release distributions will generate an artifact manifest (JSON) outside of the repository tracked paths, containing:
- Package name, version, and language
- Artifact filename and type
- SHA-256 hashes
- Size in bytes

## Release Notes Requirements
Release notes for the first public release must include:
- A statement of `baseline-public` status for Python and Node.js.
- A statement that Storage Format V1 is Stable and unchanged.
- A clear list of supported APIs and known boundaries.
- A statement explicitly noting that this is not an external security audit.

## Rollback / Yank Policy
- **When to yank:** Only in the event of severe security vulnerabilities or broken installations that affect all users immediately upon install.
- **When not to yank:** Minor bugs or backwards-compatible feature omissions should be addressed in patch releases.
- **Compatibility:** Storage Format V1 stability guarantee remains the priority.

## Post-Release Verification
After a successful publish to PyPI and npm, post-release verification will consist of:
- Clean installation from the public registry (e.g. `pip install encrypted_storage`).
- Executing the smoke tests against the installed public artifact.
- (Optional) Running the cross-language installed-distribution matrix using the downloaded artifacts.

## Explicit Non-Goals for Phase 10
- No actual publication to PyPI/npm.
- No credentials or secrets committed to the repository.
- No changes to Storage Format V1 bytes-on-disk semantics.
