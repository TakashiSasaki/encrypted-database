# Cross-Language Read/Write Compatibility Plan

## Goal
Establish a safe cross-language compatibility testing foundation across the repository implementations. This test ensures that when one language writes a Storage Format V1 payload, other languages can successfully unlock the database and read the exact same payload.

## Inventory and Current Status

| Language     | Implementation path | Current role | Read support | Write support | Stable API? | Include in this stride? | Notes |
| ------------ | ------------------- | ------------ | ------------ | ------------- | ----------- | ----------------------- | ----- |
| Python       | `python/`           | baseline     | Yes          | Yes           | Yes         | No                      | Exposes stable library API, but no automated cross-language runner yet (`EncryptedStorage`). |
| Node.js      | `nodejs/`           | baseline     | Yes          | Yes           | Yes         | No                      | Exposes stable library API, but no automated cross-language runner yet (`EncryptedStorage`). |
| Go           | `go/`               | scaffold     | Yes          | Yes           | No          | No                      | Portability validation scaffold, no stable public API. |
| Rust         | `rust/`             | scaffold     | Yes          | Yes           | No          | No                      | Portability validation scaffold, no stable public API. |
| Zig          | `zig/`              | scaffold     | Yes          | Yes           | No          | No                      | Scaffold-level CLI, not a stable storage library. |
| C            | `c/`                | scaffold     | No           | No            | No          | No                      | Parser-free JCS bootstrap scaffold only. |
| C++          | `cpp/`              | scaffold     | No           | No            | No          | No                      | Parser-free JCS bootstrap scaffold only. |

## Compatibility Matrix Dimensions
- **Supported Writers:** Python, Node.js
- **Supported Readers:** Python, Node.js
- **Active Testing Pairs:** None yet.

## Planned Fixture Format
The compatibility test creates temporary runtime SQLite databases using the standard `initialize_database` / `initializeDatabase` entrypoints. Payloads are written using `store_payload` / `storePayload`, then the same database file is passed to another language for `retrieve_payload` / `retrievePayload`.

Payload structures to be tested:
- Empty object payload: `{}`
- Small text payload: `{"message": "hello world"}`
- Binary / non-ASCII text payload: `{"data": "non-ascii: 😊 äöü"}`

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
