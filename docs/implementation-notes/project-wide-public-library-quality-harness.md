# Project-Wide Public Library Quality Harness

## Project Mission
The primary goal of this repository is to provide public-quality libraries that allow the same Storage Format V1 encrypted database to be safely written and read across multiple languages.

## Public-Quality Definition
A library is of "public quality" when it safely provides reliable read and write support using stable library APIs or CLIs that conform exactly to the Storage Format V1 bytes-on-disk semantics. It must pass all relevant cross-language compatibility matrices and shared conformance vectors. Scaffold-level read/write operations (e.g., test harnesses or internal validation utilities) do not qualify as public-quality implementations.

## Language Readiness Levels
Implementations are classified into one of the following levels:
- **baseline-public**: Fully stable, production-ready public API for read and write. Passes all matrix and conformance tests. (No languages currently meet this level).
- **baseline-candidate**: A candidate for baseline-public. Passes cross-language matrix via public-entrypoint test wrappers, but public-quality certification is pending.
- **preview-library**: Public API exists but is not yet fully stable or missing some advanced parity features.
- **portability-validation**: Scaffold implementation meant solely to validate the storage format across language boundaries. No stable public API.
- **bootstrap-scaffold**: Minimal internal implementation (like C/C++ parser-free models). Used for testing primitives or bootstrap environments. Not a storage library.
- **future**: Not yet started or planned for a later phase.

## Language Readiness Table

| Language | Implementation path | Current role | Public read support | Public write support | Scaffold read/write | Cross-read | Cross-write | Shared vectors | CI | Public package/docs | Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Python | `python/` | baseline-candidate | implemented-public* | implemented-public* | not applicable | direct-public-api-passed | direct-public-api-passed | implemented-public* | path-filtered | release-candidate | preview-library | Baseline candidate. API exists and passes execution matrix via public-entrypoint test wrappers. Still not baseline-public; public-quality certification pending. |
| Node.js | `nodejs/` | baseline-candidate | implemented-public* | implemented-public* | not applicable | direct-public-api-passed | direct-public-api-passed | implemented-public* | path-filtered | release-candidate | preview-library | Baseline candidate. API exists and passes execution matrix via public-entrypoint test wrappers. Still not baseline-public; public-quality certification pending. |
| browser-test | `browser-test/` | portability-validation | not implemented | not implemented | implemented-test-harness | deferred | deferred | implemented-test-harness | path-filtered | out-of-scope | scaffold-only | WebCrypto harness, not a full browser library. |
| Go | `go/` | portability-validation | not implemented | not implemented | implemented-scaffold | partial | missing | implemented-scaffold | path-filtered | missing | scaffold-only | Strict portability scaffold. stable public API missing; cross-language matrix not runnable; package/docs incomplete; scaffold-only or portability-only status. |
| Rust | `rust/` | portability-validation | not implemented | not implemented | implemented-scaffold | partial | missing | implemented-scaffold | path-filtered | missing | scaffold-only | Strict portability scaffold. stable public API missing; cross-language matrix not runnable; package/docs incomplete; scaffold-only or portability-only status. |
| Zig | `zig/` | portability-validation | not implemented | not implemented | implemented-scaffold | partial | missing | implemented-scaffold | path-filtered | missing | scaffold-only | Scaffold CLI only. Stable Zig version is 0.16.0. stable public API missing; cross-language matrix not runnable; package/docs incomplete; scaffold-only or portability-only status. |
| C | `c/` | bootstrap-scaffold | not implemented | not implemented | not implemented | deferred | deferred | partial | path-filtered | missing | scaffold-only | Parser-free generic JCS bootstrap scaffold only. no storage reader; no storage writer; no crypto; no SQLite storage profile; no matrix participation; only parser-free JCS/AAD/UUID-type scaffold coverage. |
| C++ | `cpp/` | bootstrap-scaffold | not implemented | not implemented | not implemented | deferred | deferred | partial | path-filtered | missing | scaffold-only | Parser-free generic JCS bootstrap scaffold only. no storage reader; no storage writer; no crypto; no SQLite storage profile; no matrix participation; only parser-free JCS/AAD/UUID-type scaffold coverage. |

## Current Matrix Status

| Language pair | Status | Reason | Evidence |
|---|---|---|---|
| Python -> Python | public-entrypoint-passed | Successfully executed direct-public-api and public-entrypoint test-wrapper matrix checks | Matrix runner (direct-public-api) |
| Node.js -> Node.js | public-entrypoint-passed | Successfully executed direct-public-api and public-entrypoint test-wrapper matrix checks | Matrix runner (direct-public-api) |
| Python -> Node.js | public-entrypoint-passed | Successfully executed direct-public-api and public-entrypoint test-wrapper matrix checks | Matrix runner (direct-public-api) |
| Node.js -> Python | public-entrypoint-passed | Successfully executed direct-public-api and public-entrypoint test-wrapper matrix checks | Matrix runner (direct-public-api) |

## Read/Write Compatibility Matrix Policy
The cross-language compatibility matrix verifies that a database created in Language A can be read with identical payload semantics by Language B.
- Scaffold-only languages are not silently treated as public libraries in this matrix.
- Unsupported language pairs are skipped with explicit reasons.
- Skipped pairs do not count as passing compatibility.
- The cross-language runner must operate on stable public APIs to count toward "baseline-public" readiness.

## Conformance Coverage Dimensions
- Writer language
- Reader language
- Payload type (empty, small string, binary data)
- Metadata shape
- Key derivation profile (Argon2id)
- AEAD envelope (AES-256-GCM)
- SQLite profile
- Expected success/failure boundaries
- Test mode

## Release-Readiness Criteria
A language implementation achieves public-quality release readiness when it has full public read/write support, passes all shared vectors, passes the cross-language compatibility matrix with all other baseline-public languages, and has complete documentation and package readiness.

## What Counts as Project-Level Progress
- Advancing a language from `preview-library` to `baseline-public`.
- Implementing and passing cross-language compatibility runner tests between baseline languages.
- Hardening shared conformance vectors that improve safety across all implementations.

## What Does Not Count as Project-Level Progress
- Improving one language or scaffold in a way that doesn't advance cross-language interoperability, public library readiness, or shared conformance.
- Adding features to scaffolds (Go/Rust/Zig/C/C++) without a path to public readiness or cross-language validation.

## Relationship to Baselines and Scaffolds
- **Python / Node.js:** Baseline candidate implementations defining the standard. Baseline-public promotion still requires CI evidence, package/docs readiness, API/error semantics review, shared vector coverage, security/release-readiness review, and cross-language evidence through stable public APIs.
- **Go / Rust / Zig:** Portability/scaffold implementations meant to validate the stability of the Storage Format V1, not to provide public APIs at this time.
- **C / C++:** Bootstrap scaffolds focusing on specific primitives (like JCS serializers) without any storage reading/writing capabilities.

* `implemented-public*` is defined as "public API surface exists" and not as release readiness, package readiness, or baseline-public certification.


For a detailed breakdown of remaining gaps, see the [Baseline-Public Readiness Gap Analysis](baseline-public-readiness-gap-analysis.md).

## Future Automation Path
The cross-language compatibility runner (`scripts/run_cross_language_compatibility.py`) is no longer discovery-only; it now actively executes the public-entrypoint test-wrapper matrix for Python and Node.js. Future work will expand it to directly bind library APIs rather than test-wrappers for final certification.
