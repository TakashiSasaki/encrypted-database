# Python/Node.js Baseline-Public Certification PR Checklist

## Scope
This checklist applies exclusively to the promotion of the Python and Node.js storage implementations to `baseline-public`. It does not apply to Go, Rust, Zig, C, C++, or any browser runtime implementation.

## Required Passing Matrices and Tests
A valid certification PR must provide execution evidence (either locally or via CI runs) for the following:

- **Direct Public API Default Execution**
  Must pass all Python/Node.js active pairs via:
  ```bash
  python scripts/run_cross_language_compatibility.py --execute
  ```

- **Explicit Public-Entrypoint-Wrapper Execution**
  Must pass all Python/Node.js active pairs via:
  ```bash
  python scripts/run_cross_language_compatibility.py --execute --mode public-entrypoint-wrapper
  ```

- **Python Tests**
  Must pass via the standard testing pipeline:
  ```bash
  cd python && python -m pip install -e ".[test]" && pytest
  ```

- **Node.js Tests**
  Must pass via the standard testing pipeline:
  ```bash
  cd nodejs && npm ci && npm test
  ```

- **Stale-Doc Guardrails**
  Must pass with no staleness identified:
  ```bash
  bash scripts/check_stale_docs.sh
  ```

## Required Review Sign-Offs
The certification PR had documented reviewer sign-off on the following items:

- [x] **API Freeze**: The public entrypoints, instantiation, lifecycle methods, and core read/write methods are frozen and aligned.
- [x] **Error Taxonomy**: The public error model and cross-language mappings are consistent and aligned.
- [x] **JCS Conformance Closure**: Active positive vectors are consumed and boundaries defined.
- [x] **Security Notes**: The limitations regarding memory zeroization and out-of-scope cryptographic claims are reviewed and accurate.
- [x] **README/Package Metadata**: Public documentation is clear, accurate, uses the correct package metadata, and disclaimers are removed.
- [x] **Storage Format V1 Non-Change**: Confirmation that absolutely no semantic changes to Storage Format V1 bytes-on-disk were made.

## Explicitly Forbidden Changes in Certification PR
The following items were **NOT** included in the baseline-public certification PR:

- No Storage Format V1 semantic changes (bytes-on-disk, JCS behavior, metadata structure).
- No changes to cryptography, AAD rules, SQLite profile behavior, or UUID generation policies.
- No production claims added for C, C++, Go, Rust, or Zig scaffolds.
- No publishing credentials, GitHub Actions release automation, or changes to PyPI/npm release pipelines.

## Certification Wording Details
Upon successful certification, the following statements became valid:
- "Python and Node.js are marked as baseline-public storage libraries."
- "Python and Node.js implementations possess public-quality certification."
- The `baseline-candidate` and `preview-library` disclaimers were removed from `python/README.md` and `nodejs/README.md`.
