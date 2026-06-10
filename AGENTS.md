# Tips for Coding Agents

This document contains guidelines and tips for coding agents working in this repository. It must be kept up-to-date with the repository's current state and long-term policies.

## Repository Structure and Status

The repository uses a monorepo setup for multi-language implementations of an encrypted database library. The `Storage Format V1` is considered **Stable**.

### Implementations

*   **Python:** Found under `python/`. This is a *baseline implementation*. Uses `cryptography` for crypto ops. Make sure to run `pip install -e .[test]` and run tests using `pytest tests/`.
*   **Node.js:** Found under `nodejs/`. This is a *baseline implementation*. Uses `better-sqlite3`, native `crypto` module, and `argon2`. Test with `npm test` via Jest. Due to ESM vs CJS support in `uuid`, we are using `uuid@9.0.1` for CommonJS compatibility in tests.
*   **browser-test:** Found under `browser-test/`. This acts as a browser/sql.js-oriented validation harness. It does *not* represent full real-browser WebCrypto runtime coverage.
*   **Go:** Found under `go/`. This is a **portability validation and writer scaffold**. It is *not* a full production storage library.
*   **Rust:** Found under `rust/`. This is a **portability validation and writer scaffold**. It is *not* a full production storage library.
*   **C:** Found under `c/`. This is an **implemented-scaffold** for a bootstrap testing environment. It is *not* a production storage library.
*   **C++:** Found under `cpp/`. This is an **implemented-scaffold** for a bootstrap testing environment. It is *not* a production storage library. Architecture is `needs-decision`.
*   **Zig:** Found under `zig/`. This is an **implemented-scaffold** for selected shared-vector conformance and SQLite read-only fixture decrypt validation. It is *not* a production storage library and lacks full public read-only parity and writer support. The target stable Zig version for the repository is strictly **0.16.0**.

## Terminology and Documentation

*   API Parity documentation must strictly use the controlled vocabulary: `implemented-public`, `implemented-test-harness`, `implemented-scaffold`, `partial`, `missing`, `out-of-scope`, `needs-decision`.
*   Documentation terminology must distinctly use **"Storage Format V1 Stable"** for the baseline format, **"Python/Node.js baseline implementation"** for mature implementations, **"Go/Rust/Zig portability validation"** or **"Go/Rust/Zig writer scaffold"** for experimental language implementations, and **"C/C++ bootstrap scaffolds"** as a distinct category for the initial native languages build environments. Do not describe the scaffolds or validations as full production storage libraries.
*   Documentation utilizing Mermaid diagrams must also explain the same information in standard text or tables.

## Cryptography and Database Constraints

*   **Argon2id Default Parameters:** When generating Argon2id parameters, always refer to `docs/providers/passphrase-argon2id.md` for the correct parameters:
    *   Time Cost (Iterations): `3`
    *   Memory Cost: `65536` KiB (64 MiB)
    *   Parallelism: `1`
*   **SQLite Constraints:**
    *   Shared SQL Schema: Handled from `docs/backend/sqlite/schema.sql`. Note that using `cross_platform` is strictly prohibited by ADR-0003; all tests must use concrete platforms such as `linux`.
    *   When using SQLite as the backend, the Node.js and Python implementations must be able to use the exact same SQLite database.
    *   `PRAGMA foreign_keys = ON` is mandatory and must be explicitly executed during database initialization or when opening connections, strictly before starting any transaction.
*   **JSON Canonicalization (JCS):** The JSON recorded in the database and the JSON before encryption must always be JCS (RFC 8785) normalized. Both the Python and Node.js implementations must strictly enforce JCS normalization. If an existing JCS normalization library is not fully compliant with the RFC, a custom JCS normalization library must be implemented and verified against all official test vectors before it is used.
*   **UUID Validation:** All Storage Format V1 metadata validators and writers enforce a strict UUID policy. UUIDs must be lowercase canonical text with an accepted version nibble (1-8) and RFC4122/RFC9562-compatible variant nibble (8, 9, a, b), exactly matching the regex `^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`.

## Scripting and Testing

*   **Test Script Execution:** The script `scripts/test_all.sh` executes the core baseline tests. It must be documented as a "baseline aggregate test command", not the "full suite", as it excludes Go, Rust, and matrix tests.
*   **Web Interfaces:** All web pages viewed in the browser, including the root `index.html` and any demo pages (e.g., in `browser-test/`), must be responsive. Use standard techniques such as CSS media queries, Flexbox, or Grid to ensure a responsive design.

## Agent Operational Guidelines

*   **Deep Planning Mode:** Always engage in a "deep planning mode" before making changes. Ask clarifying questions to test assumptions, ensure complete understanding of requirements, and wait for user answers. Create a plan and only proceed with execution autonomously after explicit user approval.
*   **PR Comments:** If GitHub Copilot or a human leaves PR review comments, you must strictly call the reply tool individually for each comment you want to reply to. Do not batch multiple replies into a single tool call due to known system limitations.
*   **Identity Verification:** Mandatory repository identity verification is required before starting work to ensure the checkout is exactly `TakashiSasaki/vault.moukaeritai.work` on the correct branch.
*   **No Temporary Files:** Final execution reports must be provided directly in chat. Never commit temporary status files (e.g., `final-report.md`), test logs, or generated database binaries to the repository.
*   **Zig Artifacts:** Zig build artifacts and compiler caches, such as `.zig-cache/` and `zig-out/`, must be explicitly ignored and never committed to the repository.
