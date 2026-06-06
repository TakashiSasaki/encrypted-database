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

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| initialize / create | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust are scaffold APIs (`CreateNew`/`create_new`). |
| open existing DB handle | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust reader/writer constructors exist, but scaffold scope. |
| close | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | All have close path, parity semantics differ. |
| lock database | implemented-public | implemented-public | implemented-test-harness | missing | missing | Go/Rust scaffold writer does not expose Python/Node-style lock state lifecycle. |
| status / state inspection | implemented-public | implemented-public | implemented-test-harness | missing | missing | No equivalent end-user status API in Go/Rust scaffold. |

### 2) Unlock and key availability

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| passphrase unlock | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust unlock is in read-only reader flow. |
| provider abstraction | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| platform provider hooks | missing | missing | missing | missing | missing | Future capability |
| recovery / fallback providers | missing | missing | missing | missing | missing | Future capability |
| key availability state | implemented-public | implemented-public | implemented-test-harness | missing | missing | Status check |

### 3) Payload operations

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| store / insert | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust store is an `implemented-scaffold` for writers. |
| retrieve / read | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust retrieval is via read-only reader API. |
| update / overwrite | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust update is an `implemented-scaffold` for writers. |
| delete / remove | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust delete is an `implemented-scaffold` for writers. |
| object UUID handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Preservation on update. |
| content type handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| metadata handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | `schema_uuid` / `content_type` support. |

### 4) Validation

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| UUID validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Strict UUID policy |
| JCS canonicalization | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Payload validation boundary. |
| provider config validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | JCS strictness. |
| metadata table validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | `storage_metadata_tbl` initialization. |
| SQLite profile validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | `PRAGMA application_id` handling. |
| required/optional feature handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| unknown feature rejection | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |

### 5) Error model

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| error categories | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Not fully standardized across languages. |
| auth failure behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| not-found behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Confirmed in write-matrix. |
| validation failure behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| provider unavailable behavior | missing | missing | missing | missing | missing | Needs implementation alongside additional providers. |
| standardized error types | partial | partial | partial | partial | partial | Error model is mostly language-specific currently. |

### 6) Transaction and persistence semantics

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| transaction boundary for operations | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| WAL/PRAGMA behavior | implemented-public | implemented-public | out-of-scope | implemented-scaffold | implemented-scaffold | Operational PRAGMAs (WAL/synchronous) are recommended, not required for V1 conformance. |
| sql.js/browser exceptions | out-of-scope | out-of-scope | implemented-test-harness | out-of-scope | out-of-scope | browser-test skips explicit file PRAGMA checks. |
| read-only mode support | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust ReadOnlyReader exists. |

### 7) Cross-language tests

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| Shared vector conformance | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Python ↔ Node roundtrip | implemented-public | implemented-public | out-of-scope | out-of-scope | out-of-scope | `integration-tests/roundtrip/` |
| browser-test parity coverage | out-of-scope | out-of-scope | implemented-test-harness | out-of-scope | out-of-scope | Does not cover export/import matrix yet. |
| Go/Rust read-only matrix | partial | partial | out-of-scope | implemented-scaffold | implemented-scaffold | Py/Node fixtures read by Go/Rust. |
| Go/Rust write-matrix | missing | missing | out-of-scope | implemented-scaffold | implemented-scaffold | Go/Rust writer outputs validated against all 4 readers. **Python and Node.js public writer APIs exist, but Python/Node writer-generated databases are not yet included in the write-matrix coverage.** |
| browser-test writer outputs matrix | out-of-scope | out-of-scope | missing | out-of-scope | out-of-scope | Browser export outputs remain future work. |

### 8) Packaging / maturity

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| public package readiness | partial | partial | out-of-scope | missing | missing | Python/Node exports/packaging needs polish. |
| CLI or library entrypoint | implemented-public | implemented-public | out-of-scope | missing | missing | |
| documentation completeness | partial | partial | partial | partial | partial | |
| production readiness status | partial | partial | out-of-scope | missing | missing | Python/Node.js are baselines; Go/Rust are purely scaffolds. |

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

## Recommended next actions

1. Extend write-matrix interoperability coverage to include Python/Node.js writer outputs against all readers.
2. Proceed to key lifecycle API design and production API polishing.
