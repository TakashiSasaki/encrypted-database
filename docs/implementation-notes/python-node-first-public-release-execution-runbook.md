# Python/Node.js First Public Release Execution Runbook

This runbook outlines the steps to execute the first public release of the `baseline-public` certified Python and Node.js packages. This document provides non-secret, non-publishing rehearsal instructions. **Actual publication, credential setup, and tag pushing are currently pending.**

*Note: Java is out-of-scope for the current Python/Node.js release stream.*

## Phases Overview
- **Phase 11: Release Candidate Freeze** (Completed: Non-publishing freeze of metadata and artifacts).
- **Phase 12: Publication Readiness Gate** (Completed: Automated checks for readiness without publishing).
- **Phase 13: Human Decision Gate** (Completed: Structured explicit authorization tracking without publishing).
- **Phase 14: Dry-Run and Registry Readiness** (Completed: Aggregated dry-run checking and unauthenticated registry probes without publishing).
- **Actual Publication** (Future explicit phase).

## Prerequisites
1. **Approval:** The publication decision must be documented and signed off in `python-node-first-public-release-decision-record.md`, replacing all `PENDING` and `PLACEHOLDER` fields.
2. **Dry Run Gate:** The repository must pass the full aggregated dry-run gate, which includes the release candidate and publication readiness gates: `scripts/run_python_node_first_public_release_dry_run.py --require-publication-ready --include-installed-matrix --allow-network-probes`.

## Step 1: Pre-execution Validation (Future)
Run the dry-run aggregator to verify approval and readiness:
```bash
python scripts/run_python_node_first_public_release_dry_run.py --require-publication-ready --include-installed-matrix --allow-network-probes
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
