# Python/Node.js First Public Release Post-Publication Verification Plan

**Note: Actual publication has not yet occurred. These are pending steps.**

Once the packages have been published to PyPI and npm, the following steps must be taken to verify their integrity and correctness in real-world environments.

## Expected Evidence Schema (Future)
For each verification step, record the following:
- **Registry:** (PyPI / npm)
- **Package:** (`encrypted_storage` / `encrypted-storage`)
- **Version:** (`0.1.0`)
- **Install Source:** (e.g., `pip install`, `npm install`)
- **Environment:** (e.g., Python 3.10 venv, Node 18 empty project)
- **Command:** (Exact execution command)
- **Result:** (Pass/Fail)
- **Artifact Hash:** (SHA-256 of downloaded tarball/wheel, if available)
- **Cross-Language Matrix Result:** (Pass/Fail across language pairs)
- **Failure Handling:** (Action taken if issues found)

## 1. Registry Inspection
- **PyPI:** Visit the PyPI project page for `encrypted_storage` and verify that the version, README, authors, license, and repository links are correctly displayed.
- **npm:** Visit the npm package page for `encrypted-storage` and verify the metadata, README, and public accessibility.

## 2. Clean Installation Test
In a completely isolated environment (outside the repository tree):

**Python:**
1. Create a clean virtual environment.
2. Install from PyPI: `pip install encrypted_storage`
3. Run a smoke test to ensure `EncryptedStorage` can be imported and initialized.

**Node.js:**
1. Create a clean, empty project directory.
2. Run `npm init -y`.
3. Install from npm: `npm install encrypted-storage`
4. Run a smoke test script to verify `EncryptedStorage` can be required and initialized.

## 3. Installed Distribution Cross-Language Matrix
Re-run the cross-language compatibility matrix using the live published packages (similar to the Phase 9 preflight, but fetching from the public registries instead of local archives).
