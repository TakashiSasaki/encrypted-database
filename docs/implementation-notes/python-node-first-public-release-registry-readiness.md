# Python/Node.js First Public Release Registry Readiness

**Phase 14 Note:** This document tracks registry-readiness decisions for the `baseline-public` Python and Node.js packages prior to explicit public release approval.

## Non-Publishing Registry Probes

The automated release gates include optional unauthenticated registry probes. These probes:
- Are completely read-only and unauthenticated.
- Are strictly opt-in via `--allow-network-probes`.
- Do **not** reserve package names.
- Do **not** prove package ownership.
- Do **not** publish any artifacts.
- Treat network failures or HTTP errors as "unknown", ensuring local gates remain stable.

## Proposed Package Names

- **PyPI:** `encrypted_storage`
- **npm:** `encrypted-storage`
- **npm (Scoped Alternative):** `@vault/encrypted-storage`

*Note: Final account/project ownership decisions for these names remain pending.*

## Pending Manual Decisions

The following human decisions are currently pending:
1. **PyPI Account/Project Ownership**
2. **npm Account/Scope Ownership**
3. **Trusted Publishing / Automation Token Strategy**
4. **Actual Release Artifact Publication**
5. **Post-Publication Verification**

## Semantics Unchanged
**Storage Format V1 Semantics:** No bytes-on-disk semantics, JCS canonical exactness, KDF profiles, AEAD limits, or UUID policies are altered.

## Future Workflow Automation

In a future stride, after trusted publishing decisions are finalized and the repository permissions are clear, a GitHub Actions workflow will be considered. At present, no GitHub Actions workflow configures secrets, publishing permissions, tag pushes, or release uploads. Future non-secret dry-run workflow planning is deferred.
