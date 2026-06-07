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

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| initialize / create | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Go/Rust are scaffold APIs (`CreateNew`/`create_new`). |
| open existing DB handle | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | Go/Rust reader/writer constructors exist, but scaffold scope. |
| close | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | All have close path, parity semantics differ. |
| lock database | implemented-public | implemented-public | implemented-test-harness | missing | missing | missing | Go/Rust scaffold writer does not expose Python/Node-style lock state lifecycle. |
| status / state inspection | implemented-public | implemented-public | implemented-test-harness | missing | missing | missing | No equivalent end-user status API in Go/Rust scaffold. |
| read-only open mode | partial | partial | missing | implemented-scaffold | implemented-scaffold | implemented-scaffold | Go/Rust have explicit `ReadOnlyReader` / `open_read_only`. Python/Node.js lack explicit read-only open mode. |

### 2) Unlock and key availability

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| passphrase unlock | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Go/Rust unlock is in read-only reader flow. |
| provider abstraction | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | |
| platform provider hooks | missing | missing | missing | missing | missing | missing | Future capability |
| recovery / fallback providers | missing | missing | missing | missing | missing | missing | Future capability |
| key availability state | implemented-public | implemented-public | implemented-test-harness | missing | missing | missing | Status check |

### 3) Payload operations

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| store / insert | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Go/Rust store is an `implemented-scaffold` for writers. |
| retrieve / read | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Go/Rust retrieval is via read-only reader API. |
| update / overwrite | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Go/Rust update is an `implemented-scaffold` for writers. |
| delete / remove | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Go/Rust delete is an `implemented-scaffold` for writers. |
| object UUID handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Preservation on update. |
| content type handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | |
| metadata handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | `schema_uuid` / `content_type` support. |
| payload listing | missing | missing | missing | missing | missing | missing | Currently no API to list payloads. |
| payload existence checks | missing | missing | missing | missing | missing | missing | Must read to check existence. |

### 4) Validation

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| UUID validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | Strict UUID policy |
| JCS canonicalization | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Payload validation boundary. |
| provider config validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | JCS strictness. |
| metadata table validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | `storage_metadata_tbl` initialization. |
| SQLite profile validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | `PRAGMA application_id` handling. |
| required/optional feature handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | |
| unknown feature rejection | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | |
| MIME/content-type validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Basic format checks. |
| schema/version validation | partial | partial | partial | partial | partial | partial | Full dynamic discovery not yet implemented. |

### 5) Error model

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| error categories | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | partial | Not fully standardized across languages. |
| auth failure behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | |
| not-found behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Confirmed in write-matrix. |
| validation failure behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | |
| provider unavailable behavior | missing | missing | missing | missing | missing | missing | Needs implementation alongside additional providers. |
| unsupported feature behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | Reject unknown. |
| SQLite/profile violation behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | implemented-scaffold | Missing/bad PRAGMAs rejected. |
| standardized error types | partial | partial | partial | partial | partial | partial | Error model is mostly language-specific currently. |

### 6) Transaction and persistence semantics

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| transaction boundary for operations | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | |
| WAL/PRAGMA behavior | implemented-public | implemented-public | out-of-scope | implemented-scaffold | implemented-scaffold | missing | Operational PRAGMAs (WAL/synchronous) are recommended, not required for V1 conformance. |
| sql.js/browser exceptions | out-of-scope | out-of-scope | implemented-test-harness | out-of-scope | out-of-scope | out-of-scope | browser-test skips explicit file PRAGMA checks. |
| rollback behavior on failure | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | Verified in unit tests. |

### 7) Cross-language tests

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| Shared vector conformance | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | missing | |
| Python ↔ Node roundtrip | implemented-public | implemented-public | out-of-scope | out-of-scope | out-of-scope | out-of-scope | `integration-tests/roundtrip/` |
| Python writer outputs matrix | partial | missing | out-of-scope | out-of-scope | out-of-scope | out-of-scope | Python public writer APIs exist, but Python writer outputs are not included in write-matrix coverage. |
| Node.js writer outputs matrix | missing | partial | out-of-scope | out-of-scope | out-of-scope | out-of-scope | Node.js public writer APIs exist, but Node.js writer outputs are not included in write-matrix coverage. |
| browser-test parity coverage | out-of-scope | out-of-scope | implemented-test-harness | out-of-scope | out-of-scope | out-of-scope | Does not cover export/import matrix yet. |
| Go/Rust read-only matrix | partial | partial | out-of-scope | implemented-scaffold | implemented-scaffold | missing | Py/Node fixtures read by Go/Rust. |
| Go/Rust write-matrix | missing | missing | out-of-scope | implemented-scaffold | implemented-scaffold | missing | Go/Rust writer outputs validated against Go/Rust/Python/Node.js readers. **Python and Node.js public writer APIs exist, but Python/Node writer-generated databases are not yet included in the write-matrix coverage.** |
| browser-test writer outputs matrix | out-of-scope | out-of-scope | missing | out-of-scope | out-of-scope | out-of-scope | Browser export/import outputs remain future work. |

### 8) Packaging / maturity

| Capability | Python | Node.js | browser-test | Go | Rust | Zig | Notes |
|---|---|---|---|---|---|---|---|
| public package readiness | partial | partial | out-of-scope | missing | missing | missing | Python/Node exports/packaging needs polish. |
| CLI or library entrypoint | implemented-public | implemented-public | out-of-scope | missing | missing | missing | |
| documentation completeness | partial | partial | partial | partial | partial | partial | |
| production readiness status | partial | partial | out-of-scope | missing | missing | missing | Python/Node.js are baselines; Go/Rust are purely scaffolds. |

## Format-level interoperability vs public API parity

- **Interoperability (Storage Format V1 Stable):** Current matrix and roundtrip harnesses show strong practical compatibility for implemented flows (notably Go/Rust writer scaffold outputs readable by Go/Rust/Python/Node.js readers, and Python↔Node.js roundtrip). Storage Format V1 is stable.
- **Public API parity:** Core store/retrieve/update/delete operations have parity across baselines. However, store/retrieve/update/delete parity does not imply full public API contract parity (lifecycle/error/provider/key-management).
- **Go/Rust scaffolds:** Go/Rust scaffold parity validates Storage Format V1 interoperability, but it is not public API contract parity with Python/Node.js.

## Language-specific notes

- **Python / Node.js**: Baseline implementations. Lifecycle, store, retrieve, update, and delete APIs are exposed publicly.
- **browser-test**: Test-harness implementation with payload operation parity. Does not represent full real-browser WebCrypto runtime coverage (it relies on sql.js and a Node `crypto` shim, not browser `crypto.subtle`).
- **Go / Rust**: Portability validation and writer scaffolds. Useful for Storage Format V1 Stable verification; not full production storage libraries.

## Known gaps

1. Go/Rust status as scaffolds means API stability/compatibility promises are intentionally limited. Go/Wasm remains an explicit target but incomplete.
2. Python and Node.js public writer APIs exist, but Python/Node writer-generated databases are not yet included in the write-matrix coverage.
3. Key lifecycle APIs, rewrap, additional unlock providers, blind index, packaging/distribution maturity, safe integer policy, schema fingerprint/hash, optional feature read-only fallback, and dynamic `created_by_version` remain future/general gaps.

## Recommended API convergence follow-ups

* `recommended-api-parity`: Standardized error taxonomy across Python/Node/browser-test/Go/Rust.
* `recommended-api-parity`: Explicit read-only open API for Python/Node.js to match Go/Rust semantics.
* `recommended-api-parity`: Consistent `status` / state inspection API and `lock`/`close` semantics across all implementations.
* `future-feature`: Payload listing and payload existence checks.
* `recommended-test-coverage`: Write-matrix expansion to include Python writer outputs.
* `recommended-test-coverage`: Write-matrix expansion to include Node.js writer outputs.
* `recommended-test-coverage`: Browser export/import real-browser runtime validation.
* `needs-decision`: Standardized error taxonomy for validation failures, auth failures, and not-found behavior.
* `future-feature`: Go/Rust public API maturation, if and only if the project wants production libraries in those languages.
