# Python/Node.js First Public Release Checklist

This document tracks the Phase 8, Phase 9, and Phase 10 release preflight readiness and outlines the final checklist before actual public publishing to PyPI and npm occurs.

## Artifact Contents Audit
- [ ] Ensure `python/dist/` contains only `.whl` and `.tar.gz` files.
- [ ] Ensure `nodejs/` tarball does not contain `.env`, `credentials`, or other unneeded secrets.
- [ ] No generated package artifacts (`.whl`, `.tar.gz`, `.tgz`) are committed.

## Version Alignment
- [ ] Python: `pyproject.toml` version matches release tag.
- [ ] Node.js: `package.json` version matches release tag.
- [ ] Both languages use identical version identifiers.

## Automated Preflight Evidence
- [x] Python distribution builds properly.
- [x] Node.js distribution builds properly.
- [x] Cross-language matrix validations passing when using installed package distributions.
- [x] Artifact hash manifest generation.

## Manual Release Approval Evidence
- [ ] PyPI project name (`encrypted_storage`) vs alternatives decided.
- [ ] npm package scope/name (`encrypted-storage` vs `@vault/encrypted-storage`) decided.
- [ ] Manual release approval gate passed.

## Clean Install Smoke Tests
- [x] Python distribution installs correctly in a clean virtual environment and smoke test passes.
- [x] Node.js distribution installs correctly in a clean test project and smoke test passes.

## PyPI/npm Project Readiness
- [ ] PyPI trusted publishing or API-token decision.
- [ ] npm trusted publishing / automation decision.
- [ ] PyPI project account or org exists.
- [ ] npm organization/scope exists.

## Package Metadata Review
- [ ] Valid `authors`, `license`, `urls` (repository URL replaces placeholders).
- [ ] README long-description correctly styled and verified.

## Release Notes & Tag Strategy
- [ ] Release artifact manifest generated properly and stored outside repo.
- [ ] Release notes drafted summarizing baseline-public features.
- [ ] Semantic versioning tag strategy established.
- [ ] Rollback/yank policy documented.
- [ ] Credential/secrets policy established for deployment.

## Matrix Validation


## Unchanged Semantics Statement
**Storage Format V1 Semantics:** No bytes-on-disk semantics, JCS canonical exactness, KDF profiles, AEAD limits, or UUID policies are altered by this release.

*Note: Actual publishing is intentionally pending and not complete.*
