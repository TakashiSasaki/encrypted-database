# Python/Node.js Baseline-Public Certification Record

## Scope
This document serves as the formal certification record for promoting the Python and Node.js implementations of Storage Format V1 to `baseline-public` status.

## Certification Decision
**Decision:** Certified.
The Python and Node.js implementations have met all requirements for `baseline-public` certification, passing all direct public API and wrapper matrix checks, unit tests, and sign-offs.

## Storage Format V1 Non-Change Statement
**This certification does NOT alter Storage Format V1 semantics.**
Bytes-on-disk semantics, metadata semantics, AAD rules, AEAD envelope layout, UUID policy, feature/version policy, SQLite profile semantics, provider_config semantics, Argon2id profile, key hierarchy, and JCS semantics remain strictly stable and unchanged.

## Certified Implementations
The following implementations are certified as `baseline-public` for Storage Format V1 read/write APIs:
*   **Python:** Passed all cross-language matrix and local unit tests.
*   **Node.js:** Passed all cross-language matrix and local unit tests.

## Excluded Implementations
The certification scope strictly excludes the following, which remain outside `baseline-public` scope:
*   `browser-test`: Out of scope (not a production storage API).
*   `Go`: Remains `portability-validation` / `scaffold`.
*   `Rust`: Remains `portability-validation` / `scaffold`.
*   `Zig`: Remains `portability-validation` / `scaffold`.
*   `C`: Remains `bootstrap-scaffold` (not a production storage library).
*   `C++`: Remains `bootstrap-scaffold` (not a production storage library).

## Evidence Summary
*   **Direct-public-api Matrix:** Passed. 4 pairs executed successfully. This serves as the primary matrix evidence.
*   **Public-entrypoint-wrapper Matrix:** Passed. 4 pairs executed successfully. This serves as secondary/supporting evidence.
*   **Python Tests:** Passed. `pytest` completed successfully (173 tests passed).
*   **Node.js Tests:** Passed. `npm test` via Jest completed successfully (132 tests passed).
*   **Aggregate Tests:** Passed. `./scripts/test_all.sh` executed successfully including integration roundtrip tests.
*   **Shared Vector Coverage:** Passed. All wired vectors (including `rfc8785-basic.json`, `generic-positive-coverage.json`, `utf16-key-ordering.json`, `uuid-v1.json`) loaded and executed cleanly.
*   **Stale-doc Guardrails:** Passed. `scripts/check_stale_docs.sh` ran successfully.
*   **API Freeze Sign-off:** Completed for the current documented Python/Node.js public API surface.
*   **Error Taxonomy Sign-off:** Completed.
*   **JCS Conformance Closure:** Completed (covers active executable vectors only; future/boundary planning vectors remain out of scope).
*   **Security Notes Sign-off:** Completed. Signed off as baseline-public readiness notes, *not* as an external security audit.

## Exact Validation Commands and Results

| Check | Command | Directory | Result | Output Excerpt/Summary |
| :--- | :--- | :--- | :--- | :--- |
| Docs Check | `bash scripts/check_stale_docs.sh` | Repo Root | **PASS** | `✅ No stale documentation phrases found.` |
| Runner Unit Tests | `python -m unittest scripts/test_run_cross_language_compatibility.py` | Repo Root | **PASS** | `Ran 6 tests ... OK (skipped=4)` |
| Runner Matrix Tests | `VAULT_RUN_COMPAT_EXECUTION_TESTS=1 python -m unittest scripts/test_run_cross_language_compatibility.py` | Repo Root | **PASS** | `Ran 6 tests ... OK` |
| Python Environment | `python -c "import sys; print(sys.executable)"` | Repo Root | **PASS** | `.../bin/python` |
| Python Setup | `python -m pip install -e "./python[test]"` | Repo Root | **PASS** | `Successfully installed...` |
| Node.js Setup | `npm ci` | `nodejs/` | **PASS** | `added 308 packages...` |
| Node.js Tests | `npm test` | `nodejs/` | **PASS** | `Test Suites: 15 passed ... Tests: 132 passed` |
| Python Tests | `pytest` | `python/` | **PASS** | `173 passed in ...` |
| Direct API Matrix | `python scripts/run_cross_language_compatibility.py --execute` | Repo Root | **PASS** | `4 pairs passed via execution matrix. ...` |
| Wrapper Matrix | `python scripts/run_cross_language_compatibility.py --execute --mode public-entrypoint-wrapper` | Repo Root | **PASS** | `4 pairs passed via execution matrix. ...` |
| Aggregate Scripts | `./scripts/test_all.sh` | Repo Root | **PASS** | `=== All Tests Completed Successfully! ===` |

## Remaining Non-Blocking Limitations
The following features are explicitly omitted from this initial `baseline-public` certification, and do not block certification:
*   No key rotation support.
*   No rewrap support.
*   No destroy support.
*   No additional unlock providers (only password).
*   No blind indexes.
*   No browser real-runtime coverage.
*   No C/C++ storage APIs.
*   Package publication / release automation is not included (no PyPI/npm automatic publish yet).

## Certification Date and HEAD Commit
*   **Date:** 2026-06-15 (UTC)
*   **Pre-certification Code Evidence HEAD Commit:** 9fd1ba09512a6ba7952ecfa675548118c35518d4 (This commit contains the code state that passed all certification validation checks. The certification documents themselves are added in the subsequent certification commit.)
