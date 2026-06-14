# Cross-Language Read/Write Compatibility Plan

## Goal
Establish a safe cross-language compatibility testing foundation across the repository implementations.

### Target Question
Can a database written by language A be read by language B with identical Storage Format V1 semantics?

## Inventory and Current Status

| Language | Implementation path | Current role | Public read support | Public write support | Scaffold read/write | Stable API? | Include in this stride? | Notes |
|---|---|---|---|---|---|---|---|---|
| Python | `python/` | baseline-candidate | known-api-unverified | known-api-unverified | N/A | existing library API used by public-entrypoint public-entrypoint test wrappers; public-quality certification pending | Yes | Exposes library API (`EncryptedStorage`). Integrated into execution matrix via wrappers. |
| Node.js | `nodejs/` | baseline-candidate | known-api-unverified | known-api-unverified | N/A | existing library API used by public-entrypoint public-entrypoint test wrappers; public-quality certification pending | Yes | Exposes library API (`EncryptedStorage`). Integrated into execution matrix via wrappers. |
| Go | `go/` | portability-validation | not implemented | not implemented | Yes | No | No | Portability validation scaffold, no stable public API. |
| Rust | `rust/` | portability-validation | not implemented | not implemented | Yes | No | No | Portability validation scaffold, no stable public API. |
| Zig | `zig/` | portability-validation | not implemented | not implemented | Yes | No | No | Scaffold-level CLI, not a stable storage library. |
| C | `c/` | bootstrap-scaffold | not implemented | not implemented | No | No | No | Parser-free generic JCS bootstrap scaffold only. |
| C++ | `cpp/` | bootstrap-scaffold | not implemented | not implemented | No | No | No | Parser-free generic JCS bootstrap scaffold only. |

## Compatibility Matrix Dimensions
- **Writer language**
- **Reader language**
- **Payload type** (empty, small string, binary data)
- **Metadata shape**
- **Key derivation profile** (Argon2id)
- **AEAD envelope** (AES-256-GCM)
- **SQLite profile**
- **Expected success/failure boundaries**
- **Test mode**

## Active Testing Pairs
Python and Node.js are actively integrated and passing the cross-language baseline test pairs through their execution public-entrypoint public-entrypoint test wrappers.
Note explicitly that wrapper success is evidence toward compatibility, not public-quality certification. See the [Baseline-Public Readiness Gap Analysis](baseline-public-readiness-gap-analysis.md) for remaining certification steps.

## Current Matrix Status

| Language pair (write -> read) | Status | Reason | Evidence |
|---|---|---|---|
| Python -> Python | public-entrypoint-test-wrapper | Successfully executed public-entrypoint public-entrypoint test wrapper checks (write/read/update/delete) | `scripts/run_cross_language_compatibility.py --execute` output |
| Node.js -> Node.js | public-entrypoint-test-wrapper | Successfully executed public-entrypoint public-entrypoint test wrapper checks (write/read/update/delete) | `scripts/run_cross_language_compatibility.py --execute` output |
| Python -> Node.js | public-entrypoint-test-wrapper | Successfully executed public-entrypoint public-entrypoint test wrapper checks (write/read/update/delete) | `scripts/run_cross_language_compatibility.py --execute` output |
| Node.js -> Python | public-entrypoint-test-wrapper | Successfully executed public-entrypoint public-entrypoint test wrapper checks (write/read/update/delete) | `scripts/run_cross_language_compatibility.py --execute` output |

*(Other combinations involving Go, Rust, Zig, C, and C++ are skipped due to lacking a stable public API and corresponding wrapper commands).*

## Planned Fixture Format
The compatibility test creates temporary runtime SQLite databases using the standard `initialize_database` / `initializeDatabase` entrypoints. Payloads are written using `store_payload` / `storePayload`, then the same database file is passed to another language for `retrieve_payload` / `retrievePayload`.

## Skipped Pair Policy
- Unsupported language pairs are skipped with explicit reasons.
- Scaffold-only languages are not silently treated as public libraries.
- C/C++ remain outside the storage read/write matrix until storage reader/writer scaffolds are explicitly implemented.
- Skipped pairs do not count as passing compatibility.

## Non-Goals
- Inventing new testing APIs for languages that do not currently have them.
- Changing Storage Format V1 bytes-on-disk semantics.
- Creating C/C++ production APIs.
- Supporting languages (Go, Rust, Zig) that only have scaffold or CLI entrypoints in this direct library API test until they offer stable library entrypoints (if ever).
- Network access or third-party dependencies outside the standard repository requirements.

## Acceptance Criteria
- Unsupported pairs are recorded as "skipped".
- Emits a clear matrix summary.
- The test operates entirely on temporary files.

## Next Safe Stride
Cross-language read/write compatibility matrix expansion.
