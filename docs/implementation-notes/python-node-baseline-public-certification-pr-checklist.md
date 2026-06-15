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
The certification PR must have documented reviewer sign-off on the following items. These items are currently marked as "ready-for-signoff" in the release candidate gate:

- [ ] **API Freeze**: The public entrypoints, instantiation, lifecycle methods, and core read/write methods are frozen and aligned.
- [ ] **Error Taxonomy**: The public error model and cross-language mappings are consistent and aligned.
- [ ] **JCS Conformance Closure**: Active positive vectors are consumed and boundaries defined.
- [ ] **Security Notes**: The limitations regarding memory zeroization and out-of-scope cryptographic claims are reviewed and accurate.
- [ ] **README/Package Metadata**: Public documentation is clear, accurate, uses the correct package metadata, and disclaimers are removed.
- [ ] **Storage Format V1 Non-Change**: Confirmation that absolutely no semantic changes to Storage Format V1 bytes-on-disk were made.

## Explicitly Forbidden Changes in Certification PR
The following items must **NOT** be included in the baseline-public certification PR. If necessary, they must be handled in separate, properly scoped PRs before or after certification.

- No Storage Format V1 semantic changes (bytes-on-disk, JCS behavior, metadata structure).
- No changes to cryptography, AAD rules, SQLite profile behavior, or UUID generation policies.
- No production claims added for C, C++, Go, Rust, or Zig scaffolds.
- No publishing credentials, GitHub Actions release automation, or changes to PyPI/npm release pipelines.

## Future Wording Details (Not Active Until Certification)
Upon successful certification, the following statements will become valid:
- "Python and Node.js will be marked as baseline-public storage libraries."
- "Python and Node.js implementations will possess public-quality certification."
- The `baseline-candidate` and `preview-library` disclaimers will be removed from `python/README.md` and `nodejs/README.md`.
- `public_quality_certification` set to `true` will be permissible in the cross-language runner evidence mode under strict conditions.

*(Note: These statements remain false during the release-candidate/preflight stride.)*
