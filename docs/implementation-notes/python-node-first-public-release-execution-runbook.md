# Python/Node.js First Public Release Execution Runbook

This runbook outlines the steps to execute the first public release of the `baseline-public` certified Python and Node.js packages. This document provides non-secret, non-publishing rehearsal instructions. **Actual publication, credential setup, and tag pushing are currently pending.**

## Prerequisites
1. **Approval:** The publication decision must be documented and signed off in the `python-node-first-public-release-decision-record.md`.
2. **Release Candidate Freeze:** The repository must be at a verified commit matching the release-candidate hash, passing the release-candidate gate.
3. **Execution Readiness Gate:** `scripts/run_python_node_publication_readiness_gate.py --require-publication-ready` must pass.

## Step 1: Pre-execution Validation
Run the execution readiness gate:
```bash
python scripts/run_python_node_publication_readiness_gate.py --require-publication-ready
```

## Step 2: Secret Management & Trusted Publishing
Configure Trusted Publishing (OIDC) or authenticate with PyPI/npm.
*Note: Do not commit tokens or credentials to the repository.*

## Step 3: Git Tagging
Create and push the semantic version tag:
(git tag commands go here)

## Step 4: Python Publication
Publish the built artifacts to PyPI:
(twine upload commands go here)

## Step 5: Node.js Publication
Publish the package to npm:
(npm publish commands go here)

## Step 6: Post-Publication Verification
Proceed to the steps outlined in `python-node-first-public-release-post-publication-verification.md` to verify the published packages.
