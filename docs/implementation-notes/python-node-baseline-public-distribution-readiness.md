# Python/Node.js Baseline-Public Distribution Readiness

## Scope
This document outlines the distribution readiness and release dry-run process for the `baseline-public` certified Python and Node.js implementations of Storage Format V1.
The scope is strictly limited to these two languages.

## Baseline-public Certification Relationship
Python and Node.js have been formally certified as `baseline-public`. Distribution readiness is the direct subsequent step to verify that the implementations can be packaged and distributed correctly without breaking semantics or dependencies.

## Non-goals
*   No actual publishing to PyPI or npm.
*   No publishing credentials added to the repository.
*   No release automation scripts requiring secrets or CI deployment keys.
*   No changes to Storage Format V1 semantics.

## Python Build Dry-run Procedure
1.  Navigate to the `python/` directory.
2.  Install the build tools: `python -m pip install build`.
3.  Run the build: `python -m build`.
4.  Verify that `dist/` contains the generated `.whl` and `.tar.gz` files.

## Python Clean Install Smoke Test Procedure
1.  Create a temporary virtual environment: `python -m venv venv-test`.
2.  Activate it: `source venv-test/bin/activate`.
3.  Install the built artifact (wheel or sdist): `pip install /path/to/encrypted_storage-*.whl` or `pip install /path/to/encrypted_storage-*.tar.gz`.
4.  Run a simple Python script to verify database initialization using the bundled schema:
    ```python
    import encrypted_storage
    storage = encrypted_storage.EncryptedStorage('test_smoke.sqlite')
    storage.initialize_database('test-password', 'linux')
    print("SUCCESS: Database initialized correctly.")
    ```
5.  Deactivate and discard the virtual environment and `test_smoke.sqlite`.

## Node.js Pack Dry-run Procedure
1.  Navigate to the `nodejs/` directory.
2.  Run the dry-run packaging: `npm pack --dry-run`.
3.  Alternatively, `npm pack` can be run to create the `.tgz` file locally.

## Node.js Clean Install Smoke Test Procedure
1.  Create a temporary test directory and run `npm init -y`.
2.  Install the packed tarball: `npm install /path/to/encrypted-storage-*.tgz`.
3.  Run a simple Node.js script to verify database initialization using the bundled schema:
    ```javascript
    const { EncryptedStorage } = require('encrypted-storage');
    async function runTest() {
        const storage = new EncryptedStorage('test_smoke.sqlite');
        await storage.initializeDatabase('test-password', 'linux');
        console.log("SUCCESS: Database initialized correctly.");
    }
    runTest();
    ```
4.  Discard the temporary test directory and `test_smoke.sqlite`.

## Cross-language Matrix Validation
If testing the matrix *after* a package install, replace the local editable or source-based installs with the compiled distribution artifacts inside a clean environment, then invoke the wrapper tests over those environments. This has been completed in the Phase 9 installed-distribution matrix preflight.

## Release Notes Checklist
- [ ] Confirm baseline-public status for included implementations.
- [ ] Document Storage Format V1 stability and unchanged semantics.
- [ ] List any notable bug fixes or known boundaries.
- [ ] Artifact hash manifest generation and verification.

## Versioning Checklist
- [ ] Python: `pyproject.toml` version matches tag.
- [ ] Node.js: `package.json` version matches tag.
- [ ] Cross-check that both maintain aligned versioning (e.g., 0.1.0).

## Artifact Handling Policy
Generated package artifacts (like `.whl`, `.tar.gz`, `.tgz`), build directories (`dist/`, `build/`, `*.egg-info`), and temporary node_modules/virtual environments must never be committed to the repository.

## Remaining Blockers Before Actual PyPI/npm Publishing
*   Manual release approval gate passed.
*   Rollback/yank policy definition.
*   Decide on GitHub Actions/CI configuration for automated releases.
*   Provision PyPI and npm organizational accounts or scopes.
*   Securely provide publish credentials to the CI environment.
*   Final review of package namespace availability (e.g., `encrypted-storage` vs scoped `@vault/encrypted-storage`).

## Phase 8 and Phase 9 Release Preflight
A non-publishing release preflight script exists at `scripts/run_python_node_release_preflight.py` to test building, packing, and smoke-testing both languages.
It creates a clean virtual environment and `npm init` environment, avoiding generated artifacts from being committed.

The preflight optionally writes an artifact hash manifest with `--write-manifest` and runs a full cross-language installed-distribution matrix with `--installed-matrix`.

Run the preflight command via:
```bash
python scripts/run_python_node_release_preflight.py
```
For machine-readable output:
```bash
python scripts/run_python_node_release_preflight.py --json
```

**Note:** Phase 8 through Phase 13 prepare for publication (candidate freeze, execution readiness, and human decision gate), not Storage Format V1 changes. No actual publishing to PyPI/npm is done.

## Storage Format V1 Non-Change Statement
**This process does NOT alter Storage Format V1 semantics.**
Bytes-on-disk semantics, metadata semantics, AAD rules, AEAD envelope layout, UUID policy, feature/version policy, SQLite profile semantics, provider_config semantics, Argon2id profile, key hierarchy, and JCS semantics remain strictly stable and unchanged.
