# Python/Node.js First Public Release Checklist

This document tracks the Phase 8 release preflight readiness and outlines the final checklist before actual public publishing to PyPI and npm occurs.

## Artifact Contents Audit
- [ ] Ensure `python/dist/` contains only `.whl` and `.tar.gz` files.
- [ ] Ensure `nodejs/` tarball does not contain `.env`, `credentials`, or other unneeded secrets.
- [ ] No generated package artifacts (`.whl`, `.tar.gz`, `.tgz`) are committed.

## Version Alignment
- [ ] Python: `pyproject.toml` version matches release tag.
- [ ] Node.js: `package.json` version matches release tag.
- [ ] Both languages use identical version identifiers.

## Package Namespace Decision
- [ ] PyPI project name (`encrypted_storage`) vs alternatives decided.
- [ ] npm package scope/name (`encrypted-storage` vs `@vault/encrypted-storage`) decided.

## Clean Install Smoke Tests
- [ ] Python distribution installs correctly in a clean virtual environment and smoke test passes.
- [ ] Node.js distribution installs correctly in a clean test project and smoke test passes.

## PyPI/npm Project Readiness
- [ ] PyPI project account or org exists.
- [ ] npm organization/scope exists.

## Package Metadata Review
- [ ] Valid `authors`, `license`, `urls` (repository URL replaces placeholders).
- [ ] README long-description correctly styled and verified.

## Release Notes & Tag Strategy
- [ ] Release notes drafted summarizing baseline-public features.
- [ ] Semantic versioning tag strategy established.
- [ ] Rollback/yank policy documented.
- [ ] Credential/secrets policy established for deployment.

## Matrix Validation
- [ ] Cross-language matrix validations passing when using installed package distributions (or explicitly deferred).

## Unchanged Semantics Statement
**Storage Format V1 Semantics:** No bytes-on-disk semantics, JCS canonical exactness, KDF profiles, AEAD limits, or UUID policies are altered by this release.

*Note: Actual publishing is intentionally pending and not complete.*
