# Tips for Coding Agents

This document contains guidelines and tips for coding agents working in this repository. It must be kept up-to-date with the repository's current state and long-term policies.


## Project Mission
The primary goal of this repository is to provide public-quality libraries that allow the same Storage Format V1 encrypted database to be safely written and read across multiple languages.

## Required Quality Gate
A change is not project-level progress merely because it improves one language or one scaffold.
Every task must report how it affects cross-language encrypted database interoperability, public library readiness, and shared conformance coverage.

Every coding task must state:
- which language implementations are affected;
- whether the change improves public read support, public write support, both, or neither;
- whether the change affects Storage Format V1 bytes-on-disk semantics;
- whether cross-language compatibility is improved, unchanged, or deferred;
- whether each affected language is baseline-public, preview-library, portability-validation, bootstrap-scaffold, or future;
- what tests were run;
- what remains outside public-quality readiness.

## Project-Wide Harness
The detailed harness lives at:
- `docs/implementation-notes/project-wide-public-library-quality-harness.md`
- `docs/implementation-notes/cross-language-read-write-compatibility-plan.md`

## Repository Structure and Status

The repository uses a monorepo setup for multi-language implementations of an encrypted database library. The `Storage Format V1` is strictly **Stable**. Any incompatible changes to storage-format semantics must be deferred to V2. Do not use terms like 'Draft' or 'Candidate', and the historical 'controlled-v1-amendment' concept is deprecated.

### Implementations

*   **Python:** Found under `python/`. This is a *baseline implementation*. Uses `cryptography` for crypto ops. Make sure to run `pip install -e .[test]` and run tests using `pytest tests/`.
*   **Node.js:** Found under `nodejs/`. This is a *baseline implementation*. Uses `better-sqlite3`, native `crypto` module, `argon2`, and `json-canonicalize` (for JCS). Test with `npm test` via Jest. Due to ESM vs CJS support in `uuid`, we are using `uuid@^9.0.1` for CommonJS compatibility in tests.
*   **browser-test:** Found under `browser-test/`. This acts as a browser/sql.js-oriented validation harness. It does *not* represent full real-browser WebCrypto runtime coverage.
*   **Go:** Found under `go/`. This is a **portability validation and writer scaffold**. It is *not* a full production storage library.
*   **Rust:** Found under `rust/`. This is a **portability validation and writer scaffold**. It is *not* a full production storage library.
*   **C:** Found under `c/`. This is an **implemented-scaffold** for a bootstrap testing environment. Built with CMake, it must not use package managers like Conan or vcpkg. It is *not* a production storage library. It provides smoke-testable entrypoints, partial AAD shared-vector conformance, internal JSON escaping for AAD construction, a limited internal generated-AST JCS basic-vector serializer scaffold, C and C++ parser-free JCS internal model scaffolds (with serializer seeds and hardened generated-vector bridges), and internal UUID syntax and content-type boundary validation through internal scaffold helpers.
*   **C++:** Found under `cpp/`. This is an **implemented-scaffold** for a bootstrap testing environment. Built with CMake, it must not use package managers like Conan or vcpkg. It is *not* a production storage library. C and C++ are independent native scaffold implementations. They provide smoke-testable entrypoints, partial AAD shared-vector conformance, internal JSON escaping for AAD construction, a limited internal generated-AST JCS basic-vector serializer scaffold, C and C++ parser-free JCS internal model scaffolds (with serializer seeds and hardened generated-vector bridges), and internal UUID syntax and content-type boundary validation through internal scaffold helpers.
*   **Zig:** Found under `zig/`. This is an **implemented-scaffold** providing a generalized scaffold CLI for reading, decrypting, and a selected SQLite V1 writer scaffold for creating and updating objects. It also retains selected fixture validation and integrates into the write-matrix. It is *not* a production storage library and lacks full public read-only parity and a stable public storage API. The target stable Zig version for the repository is strictly **0.16.0**.

## Terminology and Documentation

*   API Parity documentation must strictly use the controlled vocabulary: `implemented-public`, `implemented-test-harness`, `implemented-scaffold`, `partial`, `missing`, `out-of-scope`, `needs-decision`. Classify methods based on documented role (e.g., `implemented-scaffold` for Go/Rust/Zig) rather than strictly by language-level visibility.
*   Documentation terminology must distinctly use **"Storage Format V1 Stable"** for the baseline format, **"Python/Node.js baseline implementation"** for mature implementations, **"Go/Rust/Zig portability validation"** or **"Go/Rust/Zig writer scaffold"** for experimental language implementations, and **"C/C++ bootstrap scaffolds"** as a distinct category for the initial native languages build environments. Do not describe the scaffolds or validations as full production storage libraries.
*   Documentation utilizing Mermaid diagrams must also explain the same information in standard text or tables.
*   Prefer updating `docs/implementation-notes/api-parity-matrix.md` directly for API audits. Create `api-surface-inventory.md` only if the matrix becomes unreadably large or visually hard to maintain.
*   When documenting required follow-ups or future work in architecture and design documents, strictly use logical prerequisite ordering language (e.g., 'before implementation', 'before cryptographic use') and avoid promising timelines, dates, or estimates.
*   Embed boundary review checklists directly within the main review document (e.g., as a Markdown table) rather than creating separate checklist files, unless the document becomes excessively unwieldy.

## Cryptography and Database Constraints

*   **Argon2id Default Parameters:** When generating Argon2id parameters, always refer to `docs/providers/passphrase-argon2id.md` for the correct parameters:
    *   Time Cost (Iterations): `3`
    *   Memory Cost: `65536` KiB (64 MiB)
    *   Parallelism: `1`
    *   Salt Length: `16` bytes
*   **SQLite Constraints:**
    *   Shared SQL Schema: Handled from `docs/backend/sqlite/schema.sql`. Note that using `cross_platform` is strictly prohibited by ADR-0003; all tests must use concrete platforms such as `linux`.
    *   When using SQLite as the backend, the Node.js and Python implementations must be able to use the exact same SQLite database.
    *   `PRAGMA foreign_keys = ON` is mandatory and must be explicitly executed during database initialization or when opening connections, strictly before starting any transaction. This explicitly applies to Go, Rust, and Zig SQLite wrappers as well.
*   **JSON Canonicalization (JCS):** The JSON recorded in the database and the JSON before encryption must always be JCS (RFC 8785) normalized. Both the Python and Node.js implementations must strictly enforce JCS normalization. If an existing JCS normalization library is not fully compliant with the RFC, a custom JCS normalization library must be implemented and verified against all official test vectors before it is used. Storage Format V1 validators must strictly reject non-empty `required_features` and `optional_features`; they must exactly match the JSON string `[]`. C and C++ currently have only a limited generated-AST JCS basic-vector serializer scaffold and do not have full generic JCS, a JSON parser, or public JCS API. They also have C and C++ parser-free JCS internal model scaffolds and generic positive vector loader scaffolds (which are test-harness utilities that enforce strict fail-closed validation and do not parse JSON text). For C and C++ shared-vector tests, the project prefers using build-time Python scripts to generate test fixture headers directly into the build directory, and these generated headers are not checked into the repository. The C/C++ string model explicitly unsupported embedded NUL bytes in the first-stage generic model.
*   **UUID Validation:** All Storage Format V1 metadata validators and writers enforce a strict UUID policy. UUIDs must be lowercase canonical text with an accepted version nibble (1-8) and RFC4122/RFC9562-compatible variant nibble (8, 9, a, b), exactly matching the regex `^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`. C and C++ internal UUID syntax validation helpers enforce formatting without relying on regular expression libraries, utilizing simple and strict character and index checks instead.
*   **Metadata Validation:** Storage Format V1 metadata string fields (e.g., `created_by_library`, `created_by_version`) must not be whitespace-only. Validation across all languages must trim whitespace before checking for emptiness. This trimming rule does not apply to the `content_type` field.
*   **Content-Type Validation:** The C and C++ content-type validation scaffold enforces a minimal internal boundary rule: a non-empty string with exactly one '/', non-empty parts before/after, and no ASCII control bytes (< 0x20) or DEL (0x7f). It explicitly does not trim whitespace, lowercase, or normalize the input. The C helper must use a length-aware check to correctly reject embedded NUL bytes.

## Scripting and Testing

*   **Test Vectors:** When expanding shared JSON test vector files (e.g., `rfc8785-basic.json`), do not add new metadata fields (like `category` or `scope`) and do not rename existing vectors to avoid breaking strictly typed consumers (e.g., Rust). Store metadata and classifications strictly in documentation.
*   **Future/Unsupported Vectors:** Future and unsupported JCS boundary vectors (e.g., unsafe integers, duplicate keys, surrogate ordering, embedded NUL) must be strictly classified and stored in `test-vectors/jcs/future-boundary-plan.json` as planning-only documentation, not actively consumed test fixtures. Test harnesses across all implementations must explicitly consume `test-vectors/jcs/rfc8785-basic.json` and `test-vectors/jcs/generic-positive-coverage.json` rather than globbing the entire directory. The C/C++ JCS generated-AST generator script (`scripts/generate_jcs_test_vectors.py`) implements a schema guardrail that explicitly fails closed if it encounters vectors with planning/rejection-only keys or if the input file is named `future-boundary-plan.json`.

*   **Test Script Execution:** The script `scripts/test_all.sh` executes the core baseline tests. It must be documented as a "baseline aggregate test command", not the "full suite", as it excludes Go, Rust, and matrix tests.
*   **Web Interfaces & Verification:** All web pages viewed in the browser, including the root `index.html` and any demo pages (e.g., in `browser-test/`), must be responsive. Use standard techniques such as CSS media queries, Flexbox, or Grid to ensure a responsive design. Always dynamically update `document.title` in single-page applications (SPAs) or custom client-side viewers when the route or primary content changes to ensure accessibility for screen readers and maintain browser tab usability. Note that the root `index.html` functions as a custom single-page application (SPA) Markdown viewer for the repository's documentation. Frontend UI changes require visual verification using Playwright. You must write a Python test script (e.g., at `/home/jules/verification/verify_ux.py`), load the updated local HTML via a `file:///app/...` absolute path (the repository root is located at `/app` in the container, not `/home/jules/workspace`), take a screenshot, and call the `frontend_verification_complete` tool.
*   **C and C++ Testing:** Use CTest (`add_test`) for library-level tests and custom CMake scripts (`execute_process()`) for explicit CLI smoke tests to rigorously validate exact stdout matches and a 0 exit code. `PASS_REGULAR_EXPRESSION` must be avoided for CLI tests. The smoke test executables must output exactly `vault c smoke test ok\n` and `vault cpp smoke test ok\n`.
*   **Zig Testing:** Negative test coverage for Zig should be implemented natively via `std.testing`. Do not claim Zig tests passed unless they were actually run with the correct Zig toolchain. If the binary is unavailable in the environment, state plainly that they were not run and do not infer success by analogy.
*   **Write-Matrix Testing:** Python and Node.js write-matrix fixtures must fail closed if the target database path already exists.

*   **Cross-language Validation:** Cross-language read/write compatibility testing uses non-public, test-only wrappers (e.g., compatibility_wrapper.py, compatibility_wrapper.js) that accept parameters via CLI arguments/stdin/env and output machine-readable JSON results on stdout to the compatibility runner. The runner can discover wrapper candidates, and execution tests are environment-dependent and must be explicitly gated behind the `VAULT_RUN_COMPAT_EXECUTION_TESTS=1` environment variable. Default discovery/unit tests for the cross-language compatibility runner must remain lightweight and not require environment-dependent setups like Python editable installs, Node.js packages, native dependencies, or generated databases. Test-wrapper success is evidence of compatibility. Python and Node.js are baseline-public for Storage Format V1 read/write APIs. C/C++ remain bootstrap scaffolds outside the matrix. Go/Rust/Zig remain portability-validation/scaffold.
*   **GitHub Actions:** GitHub Actions path filters for C/C++ test workflows trigger on 'c/**', 'cpp/**', the workflow file itself, 'README.md', 'AGENTS.md', 'docs/spec/**', 'docs/implementation-notes/**', 'test-vectors/aad/**', 'test-vectors/jcs/**', 'scripts/generate_aad_test_vectors.py', and 'scripts/generate_jcs_test_vectors.py'.
*   **Documentation Guardrails:** When adding rules to `scripts/check_stale_docs.sh`, target specific, high-confidence overclaims (e.g., "all languages have full public API parity") rather than broad bans on common words. Use narrow phrase-specific checks (e.g., 'C/C++ generic serializer is implemented').
*   **Package Metadata:** For package metadata, the project standardizes on 'vault.moukaeritai.work Contributors' as the author placeholder rather than personal email addresses. Explicitly forbid 'TBD' or example.com URLs in repository or homepage fields.

## Agent Operational Guidelines

*   **Deep Planning Mode:** Always engage in a "deep planning mode" before making changes. Ask clarifying questions to test assumptions, ensure complete understanding of requirements, and wait for user answers. Create a plan and only proceed with execution autonomously after explicit user approval. When generating execution plans, the final pre-commit step must precisely match the string: 'Complete pre-commit steps to ensure proper testing, verification, review, and reflection are done.' A step explicitly running relevant tests must immediately precede this pre-commit step.
*   **PR Comments:** プルリクエストを出してから５分ほどすると、GitHub Copilotがレビューを終了しプルリクエストにコメントをつけます。レビューが終わったタイミングでレビューコメントに対応してください。対応済であることを示すためにコメントには返信してください。If GitHub Copilot or a human leaves PR review comments, you must strictly call the reply tool individually for each comment you want to reply to. Do not batch multiple replies into a single tool call due to known system limitations. プルリクエストにつけられたコメントに対応した場合には各コメントに個別にその対応結果を返信してください。複数のコメントをバッチ処理しないでください。それぞれのコメントごとに返信のためのツールを呼び出してください。
*   **Identity Verification and Cloning:** Mandatory repository identity verification is required before starting work to ensure the checkout is exactly `TakashiSasaki/vault.moukaeritai.work` on the correct branch `vault.moukaeritai.work`. 大きなリポジトリなので、depth 1 でクローンしたほうがいいかもしれないね (Recommend `depth 1` for cloning).
*   **UX Persona (Palette):** When assuming the 'Palette' UX persona, record critical UX and accessibility learnings in `.Jules/palette.md` using the exact format: `## YYYY-MM-DD - [Title]\n**Learning:** [UX/a11y insight]\n**Action:** [How to apply next time]`.
*   **GitHub Actions:** GitHub Actions workflows in the repository must be hardened by using pinned action SHAs (e.g., `actions/checkout@<sha>`).
*   **Zig Toolchain:** When downloading the Zig toolchain in an agent environment, manual tarball download (e.g., `zig-x86_64-linux-0.16.0.tar.xz`) is required. Place it outside the repository (e.g., `/tmp/zig`). Do not use `mlugg/setup-zig` action.
*   **No Temporary Files:** Final execution reports must be provided directly in chat. Never commit temporary status files (e.g., `final-report.md`), test logs, or generated database binaries to the repository.
*   **Zig Artifacts:** Zig build artifacts and compiler caches, such as `.zig-cache/` and `zig-out/`, must be explicitly ignored and never committed to the repository.
