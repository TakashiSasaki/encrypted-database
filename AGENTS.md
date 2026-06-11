# Tips for Coding Agents

This document contains guidelines and tips for coding agents working in this repository. It must be kept up-to-date with the repository's current state and long-term policies.

## Repository Structure and Status

The repository uses a monorepo setup for multi-language implementations of an encrypted database library. The `Storage Format V1` is strictly **Stable**. Any incompatible changes to storage-format semantics must be deferred to V2. Do not use terms like 'Draft' or 'Candidate', and the historical 'controlled-v1-amendment' concept is deprecated.

### Implementations

*   **Python:** Found under `python/`. This is a *baseline implementation*. Uses `cryptography` for crypto ops. Make sure to run `pip install -e .[test]` and run tests using `pytest tests/`.
*   **Node.js:** Found under `nodejs/`. This is a *baseline implementation*. Uses `better-sqlite3`, native `crypto` module, and `argon2`. Test with `npm test` via Jest. Due to ESM vs CJS support in `uuid`, we are using `uuid@9.0.1` for CommonJS compatibility in tests.
*   **browser-test:** Found under `browser-test/`. This acts as a browser/sql.js-oriented validation harness. It does *not* represent full real-browser WebCrypto runtime coverage.
*   **Go:** Found under `go/`. This is a **portability validation and writer scaffold**. It is *not* a full production storage library.
*   **Rust:** Found under `rust/`. This is a **portability validation and writer scaffold**. It is *not* a full production storage library.
*   **C:** Found under `c/`. This is an **implemented-scaffold** for a bootstrap testing environment. Built with CMake, it must not use package managers like Conan or vcpkg. It is *not* a production storage library. They share a generated AST test-vector fixture contract (`vault_jcs_internal.h`) with C++, but have independent serialization logic.
*   **C++:** Found under `cpp/`. This is an **implemented-scaffold** for a bootstrap testing environment. Built with CMake, it must not use package managers like Conan or vcpkg. It is *not* a production storage library. C and C++ are independent native scaffold implementations that share a generated AST test-vector fixture contract (`vault_jcs_internal.h`) but have independent serialization logic.
*   **Zig:** Found under `zig/`. This is an **implemented-scaffold** for a generalized read-only reader and writer scaffold, and integrates SQLite using the C ABI (`@cImport`) without vendoring. It is *not* a production storage library and lacks full public read-only parity and writer support. The target stable Zig version for the repository is strictly **0.16.0**.

## Terminology and Documentation

*   API Parity documentation must strictly use the controlled vocabulary: `implemented-public`, `implemented-test-harness`, `implemented-scaffold`, `partial`, `missing`, `out-of-scope`, `needs-decision`. Classify methods based on documented role (e.g., `implemented-scaffold` for Go/Rust/Zig) rather than strictly by language-level visibility. Python and Node.js are the closest pair for public API equivalence, whereas lifecycle and error-model APIs remain inconsistent or missing.
*   Documentation terminology must distinctly use **"Storage Format V1 Stable"** for the baseline format, **"Python/Node.js baseline implementation"** for mature implementations, **"Go/Rust/Zig portability validation"** or **"Go/Rust/Zig writer scaffold"** for experimental language implementations, and **"C/C++ bootstrap scaffolds"** as a distinct category for the initial native languages build environments. Do not describe the scaffolds or validations as full production storage libraries.
*   Documentation utilizing Mermaid diagrams must also explain the same information in standard text or tables.
*   Prefer updating `docs/implementation-notes/api-parity-matrix.md` directly for API audits. Create `api-surface-inventory.md` only if the matrix becomes unreadably large or visually hard to maintain.
*   When documenting required follow-ups or future work in architecture and design documents, strictly use logical prerequisite ordering language (e.g., 'before implementation', 'before cryptographic use') and avoid promising when work will happen by excluding timelines, dates, or estimates.
*   The C/C++ Generic JCS parser, dependency strategy, and internal value model boundary are documented as 'Proposed'. The strategy recommends a parser-free generic serializer over an internal value model first, explicitly deferring raw JSON text parsing, embedded NUL support, parser error handling, and third-party dependency additions.

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
*   **JSON Canonicalization (JCS):** The JSON recorded in the database and the JSON before encryption must always be JCS (RFC 8785) normalized. Both the Python and Node.js implementations must strictly enforce JCS normalization. If an existing JCS normalization library is not fully compliant with the RFC, a custom JCS normalization library must be implemented and verified against all official test vectors before it is used. Storage Format V1 validators must strictly reject non-empty `required_features` and `optional_features`; they must exactly match the JSON string `[]`. C and C++ currently have only a limited generated-AST JCS basic-vector serializer scaffold and do not have full generic JCS, a JSON parser, or public JCS API. Embedded NUL (`\u0000`) support in C/C++ JCS strings is marked as `needs-decision` and is not supported in the internal value model or generated-AST fixture generation due to C string-literal constraints.
*   **UUID Validation:** All Storage Format V1 metadata validators and writers enforce a strict UUID policy. UUIDs must be lowercase canonical text with an accepted version nibble (1-8) and RFC4122/RFC9562-compatible variant nibble (8, 9, a, b), exactly matching the regex `^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`. C and C++ internal UUID syntax validation helpers enforce formatting without relying on regular expression libraries, utilizing simple and strict character and index checks instead.
*   **Metadata Validation:** Storage Format V1 metadata string fields (e.g., `created_by_library`, `created_by_version`) must not be whitespace-only. Validation across all languages must trim whitespace before checking for emptiness. This trimming rule does not apply to the `content_type` field. Zig SQLite V1 validators strictly enforce `provider_config_json` JCS canonical exactness, exact profile (`argon2id-profile-v1`), kdf (`argon2id`), expected parameters (memory_kib, iterations, parallelism, output_bytes), and 16-byte unpadded base64url salt.
*   **Content-Type Validation:** The C and C++ content-type validation scaffold enforces a minimal internal boundary rule: a non-empty string with exactly one '/', non-empty parts before/after, and no ASCII control bytes (< 0x20) or DEL (0x7f). It explicitly does not trim whitespace, lowercase, or normalize the input. The C helper must use a length-aware check to correctly reject embedded NUL bytes.
*   **Shared JSON Test Vectors:** When expanding shared JSON test vector files (e.g., `rfc8785-basic.json`), do not add new metadata fields (like `category` or `scope`) and do not rename existing vectors to avoid breaking strictly typed consumers. Store metadata and classifications strictly in documentation (e.g., `jcs-vector-classification.md`).

## Scripting and Testing

*   **Test Script Execution:** The script `scripts/test_all.sh` executes the core baseline tests. It must be documented as a "baseline aggregate test command", not the "full suite", as it excludes Go, Rust, and matrix tests.
*   **Web Interfaces:** All web pages viewed in the browser, including the root `index.html` and any demo pages (e.g., in `browser-test/`), must be responsive. Use standard techniques such as CSS media queries, Flexbox, or Grid to ensure a responsive design.
*   **C and C++ Testing:** Use CTest (`add_test`) for library-level tests and custom CMake scripts (`execute_process()`) for explicit CLI smoke tests to rigorously validate exact stdout matches and a 0 exit code. `PASS_REGULAR_EXPRESSION` must be avoided for CLI tests. The smoke test executables must output exactly `vault c smoke test ok\n` and `vault cpp smoke test ok\n`.
*   **Zig Testing:** Negative test coverage for Zig should be implemented natively via `std.testing`. The Zig smoke test component must output exactly `vault zig smoke test ok` to stdout using `std.process.Init` and `std.Io.File.stdout().writeStreamingAll` (not `std.debug.print` which writes to stderr). The Zig shared vector conformance suite (`zig build vectors`) must exclusively use Zig's standard library (`std.crypto` and `std.json`) for primitives, avoiding external dependencies like libsodium.
*   **Write-Matrix Testing:** Python and Node.js write-matrix fixtures must fail closed if the target database path already exists. Cross-language write interoperability testing covers Go, Rust, Zig, Python, and Node.js. Suppressing failures as 'expected failures' is heavily discouraged without explicit logging.
*   **Documentation Guardrails:** When adding rules to `scripts/check_stale_docs.sh`, target specific, high-confidence overclaims (e.g., "all languages have full public API parity", "C/C++ generic serializer is implemented") rather than broad bans on common words like "implemented" or "generic serializer".

## Agent Operational Guidelines

*   **Deep Planning Mode:** Always engage in a "deep planning mode" before making changes. Ask clarifying questions to test assumptions, ensure complete understanding of requirements, and wait for user answers. Create a plan and only proceed with execution autonomously after explicit user approval.
*   **PR Comments:** プルリクエストを出してから５分ほどすると、GitHub Copilotがレビューを終了しプルリクエストにコメントをつけます。レビューが終わったタイミングでレビューコメントに対応してください。対応済であることを示すためにコメントには返信してください。If GitHub Copilot or a human leaves PR review comments, you must strictly call the reply tool individually for each comment you want to reply to. Do not batch multiple replies into a single tool call due to known system limitations.
*   **Identity Verification and Cloning:** Mandatory repository identity verification is required before starting work to ensure the checkout is exactly `TakashiSasaki/vault.moukaeritai.work` on the correct branch `vault.moukaeritai.work`. 大きなリポジトリなので、depth 1 でクローンしたほうがいいかもしれないね (Recommend `depth 1` for cloning).
*   **GitHub Actions:** GitHub Actions workflows in the repository must be hardened by using pinned action SHAs (e.g., `actions/checkout@<sha>`).
*   **Zig Toolchain:** When downloading the Zig toolchain in an agent environment, manual tarball download (e.g., `zig-x86_64-linux-0.16.0.tar.xz`) is required, and its SHA256 checksum must be verified. Place it outside the repository (e.g., `/tmp/zig`). Do not use `mlugg/setup-zig` action due to incorrect archive naming conventions.
*   **No Temporary Files:** Final execution reports must be provided directly in chat. Never commit temporary status files (e.g., `final-report.md`), test logs, or generated database binaries to the repository.
*   **Zig Artifacts:** Zig build artifacts and compiler caches, such as `.zig-cache/` and `zig-out/`, must be explicitly ignored and never committed to the repository.
