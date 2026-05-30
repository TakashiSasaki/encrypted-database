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
- Update/delete support is currently public in Go/Rust writer scaffolds, but not present as public APIs in Python/Node.js baseline libraries.

## Terminology / classification labels

- `implemented-public`: Exposed as normal public API for that language package.
- `implemented-internal`: Implemented but private/internal only.
- `implemented-test-only`: Exists only in test/harness code.
- `implemented-scaffold`: Implemented in portability scaffold, not production-ready API.
- `read-only-only`: Reader-only capability.
- `write-only-helper`: Writer helper path without symmetric library API.
- `verified-by-matrix`: Verified by interoperability matrix harness.
- `partially-implemented`: Only subset/conditional behavior implemented.
- `not-implemented`: No implementation found.
- `planned`: Planned in docs/spec, not implemented.
- `out-of-scope`: Explicitly outside current scope.
- `unknown-needs-decision`: Cannot classify without product/API policy decision.

## Cross-language capability matrix

### 1) Database lifecycle

| Capability | Python | Node.js | Go | Rust | Notes |
|---|---|---|---|---|---|
| Create/initialize new SQLite V1 DB | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Go/Rust are scaffold APIs (`CreateNew`/`create_new`). |
| Open existing DB handle | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Go/Rust reader/writer constructors exist, but scaffold scope. |
| Unlock database | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Go/Rust unlock is in read-only reader flow. |
| Lock database | implemented-public | implemented-public | read-only-only | read-only-only | Go/Rust scaffold writer does not expose Python/Node-style lock state lifecycle. |
| Close database | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | All have close path, parity semantics differ. |
| Status API (`is_unlocked` / `getStatus`) | implemented-public | implemented-public | not-implemented | not-implemented | No equivalent end-user status API in Go/Rust scaffold. |

### 2) Payload operations

| Capability | Python | Node.js | Go | Rust | Notes |
|---|---|---|---|---|---|
| Store/insert payload | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| Retrieve/decrypt payload | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Go/Rust retrieval is via read-only reader API. |
| Update payload | not-implemented | not-implemented | implemented-scaffold | implemented-scaffold | Python/Node have no public update API in current source. |
| Delete payload | not-implemented | not-implemented | implemented-scaffold | implemented-scaffold | Python/Node have no public delete API in current source. |
| Delete NotFound behavior | not-implemented | not-implemented | implemented-scaffold, verified-by-matrix | implemented-scaffold, verified-by-matrix | write-matrix verifies delete NotFound for Go/Rust readers only. |
| `schema_uuid`/`content_type` update support | not-implemented | not-implemented | implemented-scaffold | implemented-scaffold | Via Go/Rust `UpdatePayload`/`update_payload`. |
| `object_uuid` preservation on update | not-implemented | not-implemented | implemented-scaffold | implemented-scaffold | Verified in Go/Rust writer tests. |

### 3) Validation and canonicalization

| Capability | Python | Node.js | Go | Rust | Notes |
|---|---|---|---|---|---|
| Strict UUID validation | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| Content-Type validation | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| Payload validation boundary + JCS canonicalization | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Different API maturity; same V1 intent. |
| Passphrase validation | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| Platform validation (`cross_platform` reject) | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| `provider_config_json` JCS strictness | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Go/Rust strictness mainly in reader/scaffold validation flows. |
| Feature flags validation (`required/optional_features`) | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |

### 4) SQLite backend profile

| Capability | Python | Node.js | Go | Rust | Notes |
|---|---|---|---|---|---|
| `schema.sql` as source of truth | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | All load canonical schema file. |
| PRAGMA `application_id` / `user_version` handling | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| `page_size=4096`, `auto_vacuum=NONE`, `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON` | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Confirmed in code/tests. WAL/synchronous are operational recommendations. |

### 5) Cryptographic envelope behavior

| Capability | Python | Node.js | Go | Rust | Notes |
|---|---|---|---|---|---|
| Argon2id profile-v1 | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | Current V1 implementations and fixtures use `memory_kib=65536`, `iterations=3`, `parallelism=1`, `output_bytes=32`, and `salt_bytes=16`; this is now aligned with `docs/providers/passphrase-argon2id.md`. |
| AES-256-GCM | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| AAD policies (`wrap-database-key-v1`, `wrap-record-key-v1`, `record-payload-v1`) | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| `ciphertext || tag` storage | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| record_dek unwrap on read | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| record_dek reuse on update | not-implemented | not-implemented | implemented-scaffold | implemented-scaffold | Only applicable where update exists. |

### 6) Test / CI coverage

| Capability | Python | Node.js | Go | Rust | Notes |
|---|---|---|---|---|---|
| Shared vector conformance | implemented-public | implemented-public | implemented-scaffold | implemented-scaffold | |
| Read-only matrix (Py/Node fixtures -> Go/Rust readers) | verified-by-matrix | verified-by-matrix | verified-by-matrix | verified-by-matrix | Harness under `integration-tests/read-only-matrix/`. |
| Write-matrix updated payload read compatibility | verified-by-matrix | verified-by-matrix | verified-by-matrix | verified-by-matrix | Go/Rust writers -> all four readers. |
| Write-matrix delete NotFound compatibility | not-implemented | not-implemented | verified-by-matrix | verified-by-matrix | Delete NotFound assertions currently only for Go/Rust readers. |
| Python <-> Node roundtrip | verified-by-matrix | verified-by-matrix | out-of-scope | out-of-scope | Covered by `integration-tests/roundtrip/`. |

### 7) Unsupported future functionality

| Capability | Python | Node.js | Go | Rust | Notes |
|---|---|---|---|---|---|
| Key lifecycle APIs (rotation/decrypt_only/destruction) | planned | planned | planned | planned | Schema-capable, public APIs pending. |
| Rewrap API | planned | planned | planned | planned | |
| Additional unlock providers | planned | planned | planned | planned | Only passphrase_argon2id currently implemented. |
| Blind index API | planned | planned | planned | planned | |
| Production public API maturity guarantees | partially-implemented | partially-implemented | implemented-scaffold | implemented-scaffold | Python/Node are baseline libs; Go/Rust are portability scaffolds. |

## Storage-format interoperability vs public API parity

- **Interoperability (Storage Format V1 Stable):** Current matrix and roundtrip harnesses show strong practical compatibility for implemented flows (notably Go/Rust writer scaffold outputs readable by Go/Rust/Python/Node.js readers, and Python↔Node.js roundtrip).
- **Public API parity:** Not yet achieved. Main visible gap is update/delete API asymmetry (Go/Rust writer scaffold yes, Python/Node.js baseline implementation no).

## Language-specific notes

- **Python / Node.js:** Baseline implementations. Lifecycle and store/retrieve API are exposed publicly. Update/delete public methods are not exposed in current source.
- **Go / Rust:** Portability validation and writer scaffolds. Useful for Storage Format V1 Stable verification; not yet full production storage libraries.

## Known gaps

1. Public API asymmetry for update/delete across the four languages.
2. Go/Rust status as scaffolds means API stability/compatibility promises are intentionally limited.
3. Key lifecycle, rewrap, additional unlock providers, blind index remain planned/future.

## Recommended next actions

1. Decide target public API contract for four languages (parity design first, then implementation).
2. Implement/standardize update/delete in Python/Node (or explicitly defer and document as out-of-scope).
3. Expand write-matrix delete assertions to Python/Node readers if delete API/read behavior policy requires it.
4. After API contract alignment, proceed to key lifecycle API design and production API polishing.
