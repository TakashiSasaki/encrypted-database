# Cross-Language Compatibility Fixture Contract

## Purpose
This document defines the minimal fixture contract required for real cross-language read/write tests across the different repository implementations. The goal is to verify that a database created in Language A can be read with identical semantics by Language B, without inventing new production APIs.

## Wrapper Purpose and Non-Public Status
The test execution relies on language-specific wrapper scripts (e.g., `compatibility_wrapper.py`, `compatibility_wrapper.js`).
- These wrappers are **strictly test harness entrypoints**.
- They are **not** public APIs, product CLIs, or stable user-facing commands.
- They must use existing stable APIs but must not introduce new storage behavior solely to make the matrix pass.

## Supported Operations
- `write`: Initializes a database (if necessary), unlocks it, and writes a payload.
- `read`: Opens a database, unlocks it, retrieves a payload, and outputs it.

## Interface (CLI/Stdin/Env)
Wrappers expose a deterministic interface to the compatibility runner:

**CLI Arguments:**
- `<operation>`: `write` or `read`
- `--db <path>`: Path to the SQLite database file.
- `--schema <uuid>`: The schema UUID.
- `--content-type <type>`: The content type (e.g., `application/json`).

**Environment Variables:**
- `VAULT_PASSPHRASE`: The passphrase used to unlock the database.

**Standard Input (stdin):**
- For `write`, the JSON payload to store.
- For `read`, stdin is ignored.

## Standard Output (stdout) Format
Wrappers must output valid, machine-readable JSON on stdout.

**Successful Write:**
```json
{
  "ok": true,
  "operation": "write",
  "object_uuid": "..."
}
```

**Successful Read:**
```json
{
  "ok": true,
  "operation": "read",
  "payload": { ... }
}
```

**Failure:**
```json
{
  "ok": false,
  "operation": "write|read",
  "error": "Short description of the error"
}
```

## Standard Error (stderr) Policy
Human-readable diagnostics, logs, or debugging information must be printed to `stderr` only. This ensures the `stdout` JSON remains cleanly parseable by the compatibility runner.

## Conventions

- **Database Path Handling**: The path should be treated as an absolute or relative path to a local file. The runner will pass paths to temporary directories.
- **Passphrase**: Provided via `VAULT_PASSPHRASE` to avoid command-line leakage and escaping issues.
- **Schema UUID**: Provided via CLI, must be a standard canonical hyphenated lowercase UUID.
- **Content Type**: Provided via CLI (e.g., `application/json`).
- **JSON Payload**: Provided via stdin as a valid UTF-8 JSON string.
- **Payload Comparison**: Cross-language tests compare the *decrypted payload semantics* (the parsed JSON object), not byte-for-byte ciphertext matching, since the Storage Format V1 uses non-deterministic AEAD.

### Standard Payload Cases
The compatibility runner should exercise at minimum the following payloads:
1. `{}` (Empty object)
2. `{"message":"hello world"}` (Simple ASCII string)
3. `{"message":"こんにちは"}` (Non-ASCII UTF-8 string)
4. `{"nested":{"array":[null,true,42,"text"]}}` (Nested structures and mixed types)

## Temporary File and Artifact Policy
- The runner must use temporary directories for databases.
- Generated artifacts must **not** be committed to the repository.
- Each write/read pair test should run in a clean, isolated temporary environment.

## Success/Failure Behavior & Runner Interpretation
- If a wrapper exits with a non-zero status, or `ok` is `false`, the pair test is considered **failed**.
- If a wrapper cannot be invoked (e.g., script not found, missing dependencies), the pair may be **skipped** if explicitly unconfigured, but if execution is requested and fails, it is a failure.
- The runner must compare the retrieved payload against the originally written payload. If they do not match semantically, the test **failed**.
- If all steps succeed and payloads match, the test **passed**.

## Skipped-Pair Policy
- Pairs where a language lacks a stable library API (e.g., Go, Rust, Zig, C, C++) are **skipped** and reported as `scaffold-only`.
- If an implementation exists but a wrapper cannot be run (e.g., test runner not set up), it is marked as `not-yet-runnable` and **skipped**.
- Skipped pairs **must never** count as passed.
