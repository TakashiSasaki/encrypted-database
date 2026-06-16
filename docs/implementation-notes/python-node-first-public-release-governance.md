# First Public Release Governance

This document establishes the governance policies for the upcoming first public release of the `baseline-public` certified Python and Node.js implementations.

## Publication Status Statement
**Important:** This repository stride does NOT publish any packages. Actual publication remains pending. The release preflight tooling is purely for local validation and dry-run artifact generation.

## Future Actual Release PR Requirements
When an actual release PR is opened, it must contain:
1. Final namespace/account selections for PyPI and npm.
2. Verified semantic versioning tags.
3. Explicit release notes.
4. A signed-off artifact hash manifest.
5. If using CI deployment: GitHub Actions workflow code utilizing trusted publishing (OIDC) or explicitly defined secrets policy.

## Who/What Performs Publishing
Publishing shall be performed either by:
- A designated human maintainer running `twine` / `npm publish` locally (for the initial release).
- A credentialed CI runner using strictly scoped PyPI/npm tokens or OIDC trusted publishing.

## Never-Commit Rules
The following items must NEVER be committed to the repository:
1. Real publishing credentials, API tokens, `.env` secrets, or look-alike placeholders.
2. Generated artifacts (`.whl`, `.tar.gz`, `.tgz`).
3. Build caches (`dist/`, `build/`, `*.egg-info`, `node_modules/`).
4. Smoke test SQLite databases.

## Trusted Publishing vs Token-Based Publishing
The project strongly recommends **Trusted Publishing (OIDC)** for GitHub Actions to PyPI and npm provenance to avoid long-lived credentials. If API tokens are required, they must be scoped to the specific package and strictly stored in GitHub Repository Secrets.

## Rollback / Yank Policy Outline
If a published package is found to have a critical defect:
1. **PyPI:** The release must be "yanked" on PyPI immediately. A new patch version must be pushed. We do not delete releases to preserve immutability.
2. **npm:** The release must be deprecated (`npm deprecate`). We avoid `npm unpublish` if more than 72 hours have passed, to prevent breaking downstream users. A new patch version must be published.

## Artifact Retention Policy
Preflight and dry-run artifacts are considered ephemeral and should be discarded after validation. Final release artifacts published to PyPI/npm are retained indefinitely by those package registries. The repository will not serve as an artifact host.

## Tag Policy
All releases must correspond to an immutable Git tag following semantic versioning (e.g., `v0.1.0`). The tag must point to the exact commit used to build the published artifacts.

## Storage Format V1 Non-Change Statement
**No bytes-on-disk semantics are changed by this release.**
Storage Format V1 remains stable. Metadata semantics, provider_config semantics, JCS rules, AAD rules, AEAD envelope layout, UUID policy, feature/version policy, SQLite Storage Profile semantics, Argon2id profile, key hierarchy, and cryptographic algorithms are strictly preserved.
