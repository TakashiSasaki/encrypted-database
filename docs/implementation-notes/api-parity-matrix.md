# API Parity Matrix

## Scope

This document audits the current **implemented surface** across Python / Node.js / Go / Rust for Storage Format V1 Stable.
It intentionally separates:

1. **Storage-format interoperability parity** (can language A read/write V1 data that language B produced?)
2. **Public library API parity** (can application developers use equivalent APIs in each language?)

## Summary

- Storage Format V1 Stable interoperability is materially validated for current implemented paths (especially Python/Node.js baseline implementations and Go/Rust portability validation writer scaffolds).
- Public API parity is **not** complete across four languages. (Note: This public API incompleteness does not weaken the Storage Format V1 Stable baseline).
- Python and Node.js expose baseline storage library APIs (initialize/open/unlock/store/retrieve/lock/close/status).
- Go and Rust currently expose portability validation and writer scaffolds; they are **not full production storage libraries** yet.
- Core payload operation parity is largely achieved across Python, Node.js, and browser-test implementations.
- Update/delete support is implemented and public across Python, Node.js, and browser-test, and remains scaffolded in Go/Rust.
- Go/Wasm is an explicit development target, though current support is blocked by SQLite driver constraints (see `go-wasm.md`).

## Terminology / classification labels

- `implemented-public`: Exposed as normal public API for that language package.
- `implemented-test-harness`: Implemented for browser-test or integration validation, not a production public API.
- `implemented-scaffold`: Implemented for portability validation or writer/readers scaffolding, not production public API.
- `partial`: Materially present but incomplete or missing important API-contract behavior.
- `missing`: Not implemented.
- `out-of-scope`: Explicitly outside current scope.
- `needs-decision`: Unclear from current code/docs and requires maintainer decision.

## Cross-language capability matrix

### 1) Database lifecycle

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| Create/initialize new SQLite V1 DB | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust are scaffold APIs (`CreateNew`/`create_new`). |
| Open existing DB handle | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust reader/writer constructors exist, but scaffold scope. |
| Unlock database | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust unlock is in read-only reader flow. |
| Lock database | implemented-public | implemented-public | implemented-test-harness | missing | missing | Go/Rust scaffold writer does not expose Python/Node-style lock state lifecycle. |
| Close database | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | All have close path, parity semantics differ. |
| Status API (`is_unlocked` / `getStatus`) | implemented-public | implemented-public | implemented-test-harness | missing | missing | No equivalent end-user status API in Go/Rust scaffold. |

### 2) Payload operations

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| Store/insert payload | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Retrieve/decrypt payload | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust retrieval is via read-only reader API. |
| Update payload | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Delete payload | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Delete NotFound behavior | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Verified by write-matrix for all readers. |
| `schema_uuid`/`content_type` update support | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| `object_uuid` preservation on update | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |

### 3) Validation and canonicalization

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| Strict UUID validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Content-Type validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Payload validation boundary + JCS canonicalization | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Different API maturity; same V1 intent. |
| Passphrase validation | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Platform validation (`cross_platform` reject) | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| `provider_config_json` JCS strictness | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Go/Rust strictness mainly in reader/scaffold validation flows. |
| Feature flags validation (`required/optional_features`) | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |

### 4) SQLite backend profile

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| `schema.sql` as source of truth | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | All load canonical schema file. |
| PRAGMA `application_id` / `user_version` handling | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| `page_size=4096`, `auto_vacuum=NONE`, `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON` | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Confirmed in code/tests. `foreign_keys=ON` is mandatory. `page_size=4096` and `auto_vacuum=NONE` are initialization requirements. WAL/synchronous are operational recommendations, not conformance invariants. |

### 5) Cryptographic envelope behavior

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| Argon2id profile-v1 | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | Current V1 implementations and fixtures use `memory_kib=65536`, `iterations=3`, `parallelism=1`, `output_bytes=32`, and `salt_bytes=16`; this is now aligned with `docs/providers/passphrase-argon2id.md`. |
| AES-256-GCM | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| AAD policies (`wrap-database-key-v1`, `wrap-record-key-v1`, `record-payload-v1`) | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| `ciphertext || tag` storage | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| record_dek unwrap on read | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| record_dek reuse on update | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold |  |

### 6) Test / CI coverage

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| Shared vector conformance | implemented-public | implemented-public | implemented-test-harness | implemented-scaffold | implemented-scaffold | |
| Read-only matrix (Py/Node fixtures -> Go/Rust readers) | partial | partial | out-of-scope | partial | partial | CI harness under `integration-tests/read-only-matrix/`. |
| Write-matrix updated payload read compatibility | partial | partial | out-of-scope | partial | partial | Go/Rust writers -> all four readers. Python and Node.js public writer APIs exist, but the write-matrix currently validates Go/Rust writer outputs against available readers. Adding Python/Node.js writer-generated databases to the write-matrix remains a recommended coverage expansion. |
| Write-matrix delete NotFound compatibility | partial | partial | out-of-scope | partial | partial | Confirmed in write-matrix for Go/Rust outputs. Python and Node.js outputs are missing / recommended expansion. |
| Python <-> Node roundtrip | partial | partial | out-of-scope | out-of-scope | out-of-scope | Covered by `integration-tests/roundtrip/`. |

### 7) Unsupported future functionality

| Capability | Python | Node.js | browser-test | Go | Rust | Notes |
|---|---|---|---|---|---|---|
| Key lifecycle APIs (rotation/decrypt_only/destruction) | missing | missing | missing | missing | missing | Schema-capable, public APIs pending. |
| Rewrap API | missing | missing | missing | missing | missing | |
| Additional unlock providers | missing | missing | missing | missing | missing | Only passphrase_argon2id currently implemented. |
| Blind index API | missing | missing | missing | missing | missing | |
| Production public API maturity guarantees | partial | partial | out-of-scope | missing | missing | Python/Node are baseline libs; Go/Rust are portability scaffolds. |

## Format-level interoperability vs public API parity

- **Interoperability (Storage Format V1 Stable):** Current matrix and roundtrip harnesses show strong practical compatibility for implemented flows (notably Go/Rust writer scaffold outputs readable by Go/Rust/Python/Node.js readers, and Python↔Node.js roundtrip).
- **Public API parity:** Largely achieved for core store/retrieve/update/delete operations.

## Language-specific notes

- **Python / Node.js**: Baseline implementations. Lifecycle, store, retrieve, update, and delete APIs are exposed publicly.
- **browser-test**: Test-harness implementation with payload operation parity. Does not represent full real-browser WebCrypto runtime coverage.
- **Go / Rust**: Portability validation and writer scaffolds. Useful for Storage Format V1 Stable verification; not full production storage libraries. Go/Rust scaffold parity validates Storage Format V1 interoperability, but it is not public API contract parity with Python/Node.js.

## Known gaps

1. Go/Rust status as scaffolds means API stability/compatibility promises are intentionally limited.
2. Key lifecycle, rewrap, additional unlock providers, blind index remain planned/future.

## Recommended next actions

1. Extend write-matrix interoperability coverage to include Python/Node.js writer outputs against all readers.
2. Proceed to key lifecycle API design and production API polishing.
