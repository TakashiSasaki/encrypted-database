# Python/Node.js First Public Release Execution Runbook

This runbook outlines the steps to execute the first public release of the `baseline-public` certified Python and Node.js packages. This document provides non-secret, non-publishing rehearsal instructions. **Actual publication, credential setup, and tag pushing are currently pending.**

## Phases Overview
- **Phase 11: Release Candidate Freeze** (Completed: Non-publishing freeze of metadata and artifacts).
- **Phase 12: Publication Readiness Gate** (Completed: Automated checks for readiness without publishing).
- **Phase 13: Human Decision Gate** (Completed: Structured explicit authorization tracking without publishing).
- **Actual Publication** (Future explicit phase).

## Prerequisites
1. **Approval:** The publication decision must be documented and signed off in `python-node-first-public-release-decision-record.md`, replacing all `PENDING` and `PLACEHOLDER` fields.
2. **Release Candidate Freeze:** The repository must be at a verified commit matching the release-candidate hash, passing the Phase 11 release-candidate gate (`scripts/run_python_node_release_candidate_gate.py`).
3. **Execution Readiness Gate:** `scripts/run_python_node_publication_readiness_gate.py --require-publication-ready` must pass.

## Step 1: Pre-execution Validation (Future)
Run the execution readiness gate to verify approval and readiness:
```bash
python scripts/run_python_node_publication_readiness_gate.py --require-publication-ready
```

## Step 2: Secret Management & Trusted Publishing (Future)
*Note: Do not commit tokens or credentials to the repository.*
Configure Trusted Publishing (OIDC) or authenticate with PyPI/npm.

## Step 3: Git Tagging (Future)
Create and push the semantic version tag:
*(Git tag commands after explicit approval)*

## Step 4: Python Publication (Future)
Publish the built artifacts to PyPI:
*(Twine upload commands after explicit approval)*

## Step 5: Node.js Publication (Future)
Publish the package to npm:
*(npm publish commands after explicit approval)*

## Step 6: Post-Publication Verification (Future)
Proceed to the steps outlined in `python-node-first-public-release-post-publication-verification.md` to verify the published packages.
