# Go WebAssembly (Wasm) Target

Go/Wasm is an **explicit development target** for the Storage Format V1 implementation. The goal is to allow browser and other WebAssembly runtimes to securely interact with the format.

## Current Status

Currently, the primary obstacle to building the complete Go package (including the SQLite backend) for the `js/wasm` target is its dependency on CGO or C-transpiled components.

When running:
```bash
GOOS=js GOARCH=wasm go test ./...
```
The test suite fails during setup due to `exec format error` and constraints in the `modernc.org/libc` package used by the `modernc.org/sqlite` driver. The driver relies on C code constructs that are not natively compatible with pure Go Wasm without additional tooling or alternatives.

## Non-SQLite Feasibility
Non-SQLite packages (like `internal/jcs`, `internal/base64url`, and `internal/aad`) theoretically lack CGO dependencies, but currently cannot be tested independently with `GOOS=js GOARCH=wasm go test .` due to the lack of test files or isolated executable tests in those directories, or similar environment errors.

## SQLite Reader/Writer Feasibility
The `internal/sqlitev1` implementation cannot currently compile to Wasm because of the `modernc.org/sqlite` driver limitation. Replacing this driver or adding a Wasm-specific database backend is outside the scope of current parity tasks.

## Next Steps
- Establish isolated tests for pure-Go cryptographic and canonicalization components (JCS, base64url, AAD).
- Investigate SQLite driver alternatives or CGO/Wasm build pipelines (e.g., `sqlite3-wasm` wrappers) capable of providing pure-Wasm compatible SQL operations.
