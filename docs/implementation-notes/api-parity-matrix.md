# API Parity Matrix

This document tracks the implementation status of the public API contract across different language bindings and environments.

## Classification Model

The following controlled vocabulary is strictly used to classify API implementation maturity:

- `implemented-public`: Exposed as normal public API for that language package. Intended for normal library use.
- `implemented-test-harness`: Implemented for browser-test or integration validation, not a production public API.
- `implemented-scaffold`: Implemented for portability validation or writer/readers scaffolding, not production public API.
- `partial`: Materially present but incomplete or missing important API-contract behavior.
- `missing`: Not implemented.
- `out-of-scope`: Intentionally not part of that component's role.
- `needs-decision`: Unclear from current code/docs and requires maintainer decision.

## Cross-language capability matrix

### 1) Database lifecycle

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| initialize / create | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust/Zig are scaffold APIs (`CreateNew`/`create_new`/`createNew`). |
| open existing DB handle | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust reader/writer constructors exist, but scaffold scope. |
| close | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | All have close path, parity semantics differ. |
| lock database | implemented-public | implemented-public | implemented-test-harness | missing | missing | missing | missing | missing | Go/Rust scaffold writer does not expose Python/Node-style lock state lifecycle. |
| status / state inspection | implemented-public | implemented-public | implemented-test-harness | missing | missing | missing | missing | missing | No equivalent end-user status API in Go/Rust scaffold. |
| read-only open mode | partial | partial | missing | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust have explicit `ReadOnlyReader` / `open_read_only`. Python/Node.js lack explicit read-only open mode. |

### 2) Unlock and key availability

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| passphrase unlock | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | partial | missing | missing | Go/Rust unlock is in read-only reader flow. Zig can unlock selected fixtures but does not expose a public unlock API. |
| provider abstraction | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | partial | missing | missing | Zig only supports passphrase_argon2id in its read-only scaffold. |
| platform provider hooks | missing | missing | missing | missing | missing | missing | missing | missing | Future capability |
| recovery / fallback providers | missing | missing | missing | missing | missing | missing | missing | missing | Future capability |
| key availability state | implemented-public | implemented-public | implemented-test-harness | missing | missing | missing | missing | missing | Status check |

### 3) Payload operations

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| store / insert | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust/Zig provide `implemented-scaffold` for writers. |
| retrieve / read | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust retrieval is via read-only reader API. Zig has a generalized read-only scaffold CLI. |
| update / modify | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust/Zig update is an `implemented-scaffold` for writers. |
| delete / remove | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust/Zig delete is an `implemented-scaffold` for writers. |
| object UUID handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | partial | partial | Preservation on update. C/C++ have internal format validation helpers. |
| content type handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | partial | partial | Zig carries these through read result. C/C++ have internal format validation helpers. |
| metadata handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | `schema_uuid` / `content_type` support. Zig carries these through read result. |
| payload listing | missing | missing | missing | missing | missing | missing | missing | missing | Currently no API to list payloads. |
| payload existence checks | missing | missing | missing | missing | missing | missing | missing | missing | Must read to check existence. |

### 4) Validation

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| UUID validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | partial | partial | Strict UUID policy. C/C++ have internal helpers. |
| JCS canonicalization | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | partial | partial | C/C++ have an internal generated-AST JCS basic-vector serializer scaffold only; no JSON parser, full RFC 8785 implementation, or public JCS API. |
| provider config validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | JCS strictness. |
| metadata table validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | `storage_metadata_tbl` initialization. |
| SQLite profile validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | `PRAGMA application_id` handling. |
| required/optional feature handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | |
| unknown feature rejection | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | |
| MIME/content-type validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | partial | partial | Basic format checks. C/C++ have internal helpers only. |
| schema/version validation | partial | partial | partial | partial | partial | partial | missing | missing | Full dynamic discovery not yet implemented. |
| internal format validation helpers | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | partial | partial | C and C++ provide internal UUID syntax validation and content-type boundary validation helpers. |

### 5) Error model

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| error categories | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | partial | missing | missing | Not fully standardized across languages. |
| auth failure behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Zig handles this via `KeyUnwrapFailed` internally. |
| not-found behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Confirmed in write-matrix. Zig handles this via `ObjectNotFound`. |
| validation failure behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | |
| provider unavailable behavior | missing | missing | missing | missing | missing | missing | missing | missing | Needs implementation alongside additional providers. |
| unsupported feature behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Reject unknown. |
| SQLite/profile violation behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Missing/bad PRAGMAs rejected. |
| standardized error types | partial | partial | partial | partial | partial | partial | missing | missing | Error model is mostly language-specific currently. |

### 6) Transaction and persistence semantics

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| transaction boundary for operations | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | |
| WAL/PRAGMA behavior | implemented-public | implemented-public | out-of-scope | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Operational PRAGMAs (WAL/synchronous) are recommended, not required for V1 conformance. |
| sql.js/browser exceptions | out-of-scope | out-of-scope | implemented-test-harness | out-of-scope | out-of-scope | out-of-scope | missing | missing | browser-test skips explicit file PRAGMA checks. |
| rollback behavior on failure | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Verified in unit tests. |

### 7) Cross-language tests

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| Shared vector conformance | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | partial | partial | C and C++ support AAD shared-vector conformance via scaffold helpers. |
| Python ↔ Node roundtrip | implemented-public | implemented-public | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | `integration-tests/roundtrip/` |
| Python writer outputs matrix | partial | missing | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | Python writer outputs are validated against Go/Rust/Zig/Python/Node.js readers. |
| Node.js writer outputs matrix | missing | partial | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | Node.js writer outputs are validated against Go/Rust/Zig/Python/Node.js readers. |
| browser-test parity coverage | out-of-scope | out-of-scope | implemented-test-harness | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | Does not cover export/import matrix yet. |
| Go/Rust read-only matrix | partial | partial | out-of-scope | implemented-scaffold | implemented-scaffold | partial | missing | missing | Py/Node fixtures read by Go/Rust/Zig. Zig support provides read-only CLI and fixture coverage. |
| Go/Rust/Zig write-matrix | missing | missing | out-of-scope | implemented-scaffold | implemented-scaffold | implemented-scaffold | missing | missing | Go/Rust/Zig/Python/Node writer outputs are validated against Go/Rust/Zig/Python/Node readers. This improves Storage Format V1 interoperability validation. |
| browser-test writer outputs matrix | out-of-scope | out-of-scope | missing | out-of-scope | out-of-scope | out-of-scope | out-of-scope | out-of-scope | Browser export/import outputs remain future work. |

### 8) Packaging / maturity

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | C | C++ | Notes |
|---|---|---|---|---|---|---|---|---|---|
| public package readiness | partial | partial | out-of-scope | missing | missing | missing | missing | missing | Python/Node exports/packaging needs polish. |
| CLI or library entrypoint | implemented-public | implemented-public | out-of-scope | missing | missing | missing | implemented-scaffold | implemented-scaffold | |
| documentation completeness | partial | partial | partial | partial | partial | partial | partial | partial | |
| production readiness status | partial | partial | out-of-scope | missing | missing | missing | missing | missing | Python/Node.js are baselines; Go/Rust/Zig/C/C++ are purely scaffolds. |

## Format-level interoperability vs public API parity

- **Interoperability (Storage Format V1 Stable):** Current matrix and roundtrip harnesses show strong practical compatibility for implemented flows (notably Go/Rust writer scaffold outputs readable by Go/Rust/Python/Node.js readers, and Python↔Node.js roundtrip). Storage Format V1 is stable.
- **Public API parity:** Core store/retrieve/update/delete operations have parity across baselines. However, store/retrieve/update/delete parity does not imply full public API contract parity (lifecycle/error/provider/key-management).
- **Go/Rust scaffolds:** Go/Rust scaffold parity validates Storage Format V1 interoperability, but it is not public API contract parity with Python/Node.js.

## Language-specific notes

- **Python / Node.js**: Baseline implementations. Lifecycle, store, retrieve, update, and delete APIs are exposed publicly.
- **browser-test**: Test-harness implementation with payload operation parity. Does not represent full real-browser WebCrypto runtime coverage (it relies on sql.js and a Node `crypto` shim, not browser `crypto.subtle`).
- **Go / Rust**: Portability validation and writer scaffolds. Useful for Storage Format V1 Stable verification; not full production storage libraries.
- **C / C++**: Bootstrap scaffolds only. They currently provide smoke-testable CLI/library entrypoints, partial AAD shared-vector conformance, internal JSON escaping for AAD construction, an internal generated-AST JCS basic-vector serializer scaffold, internal UUID syntax validation, and internal content-type boundary validation. They do not implement Storage Format V1 cryptography, SQLite read/write support, or production public APIs. C++ architecture relative to C remains `needs-decision`.

## Known gaps

1. Go/Rust status as scaffolds means API stability/compatibility promises are intentionally limited. Go/Wasm remains an explicit target but incomplete.
2. Python および Node.js によって生成されたデータベースは、現在 write-matrix の検証カバレッジに含まれています。
3. Key lifecycle APIs, rewrap, additional unlock providers, blind index, packaging/distribution maturity, safe integer policy, schema fingerprint/hash, optional feature read-only fallback, and dynamic `created_by_version` remain future/general gaps.

## Recommended API convergence follow-ups

* `recommended-api-parity`: Standardized error taxonomy across Python/Node/browser-test/Go/Rust.
* `recommended-api-parity`: Explicit read-only open API for Python/Node.js to match Go/Rust semantics.
* `recommended-api-parity`: Consistent `status` / state inspection API and `lock`/`close` semantics across all implementations.
* `future-feature`: Payload listing and payload existence checks.
* `recommended-test-coverage`: Browser export/import real-browser runtime validation.
* `needs-decision`: Standardized error taxonomy for validation failures, auth failures, and not-found behavior.
* `future-feature`: Go/Rust public API maturation, if and only if the project wants production libraries in those languages.
