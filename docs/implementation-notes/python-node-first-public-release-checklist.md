# Python/Node.js First Public Release Checklist

This document tracks Phase 8 through Phase 14 release preflight, execution readiness, human decision gate, and dry-run registry readiness, outlining the final checklist before actual public publishing to PyPI and npm occurs.

*Note: Java is out-of-scope for the current Python/Node.js release stream.*

## Completed Automated Evidence
- [x] Python distribution builds properly.
- [x] Node.js distribution builds properly.
- [x] Cross-language matrix validations passing when using installed package distributions.
- [x] Artifact hash manifest generation.
- [x] Python distribution installs correctly in a clean virtual environment and smoke test passes.
- [x] Node.js distribution installs correctly in a clean test project and smoke test passes.

## Release-Candidate Freeze Evidence (Phase 11)
- [x] Python: `pyproject.toml` version matches candidate version.
- [x] Node.js: `package.json` version matches candidate version.
- [x] Both languages use identical version identifiers (`0.1.0`).
- [x] Package metadata validated by release-candidate gate.
- [x] Release-candidate gate script added and passing locally.
- [x] Release notes draft prepared as RC-safe.
- [x] Local artifact/report generation policy verified (no generated artifacts committed).
- [x] `python/dist/` contains no tracked `.whl` or `.tar.gz` files.
- [x] `nodejs/` tarball generation path is clean of committed artifacts.

## Phase 12 Execution Readiness Evidence
- [x] Publication readiness gate script added.
- [x] Release execution runbook documented.
- [x] Post-publication verification plan documented.

## Phase 13 Human Decision Gate Evidence
- [x] Human approval packet added.
- [x] Decision record made machine-checkable.
- [x] Decision gate added/hardened.
- [x] Decision gate tests added/hardened.
- [x] Docs updated for Phase 13.

## Phase 14 Dry-Run & Registry-Readiness Evidence
- [x] Publication readiness gate hardened with explicit TOML/JSON metadata validation.
- [x] Unauthenticated registry probes implemented (opt-in).
- [x] Dry-run aggregator script and tests added.
- [x] Registry-readiness documentation added.
- [x] Stale-doc guardrails updated to prevent false Phase 14 claims.
- [x] Docs updated for Phase 14.

## Manual Approval Evidence (Pending)
- [ ] PyPI project name (`encrypted_storage`) vs alternatives decided.
- [ ] npm package scope/name (`encrypted-storage` vs `@vault/encrypted-storage`) decided.
- [ ] Manual release manager approval gate passed.

## Registry & Account Readiness (Pending)
- [ ] PyPI trusted publishing or API-token decision.
- [ ] npm trusted publishing / automation decision.
- [ ] PyPI project account or org exists.
- [ ] npm organization/scope exists.

## Publication Execution Evidence (Pending)
- [ ] Release artifact manifest generated properly and stored outside repo.
- [ ] Semantic versioning tag created.
- [ ] Rollback/yank policy documented and approved.
- [ ] Actual PyPI publication.
- [ ] Actual npm publication.
- [ ] Post-publication verification against public registries.

## Unchanged Semantics Statement
**Storage Format V1 Semantics:** No bytes-on-disk semantics, JCS canonical exactness, KDF profiles, AEAD limits, or UUID policies are altered by this release.

*Note: Actual publishing is intentionally pending and not complete.*
