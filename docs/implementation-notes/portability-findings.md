# Portability Findings Log

This log tracks issues discovered during the Go and Rust portability validation phase.
Go/Rust portability validation is performed relative to the `tag-1.z.z` Storage Format V1 stable baseline.

## Findings

| ID | Date | Area | Observed in | Issue | Classification | Impact | Decision | Status | Related files/tests |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

## Expected Watch Areas
The following areas are anticipated points of divergence and should be monitored closely during the Go and Rust implementations:

- JCS canonicalization differences
- JSON number / safe integer handling
- UTF-8 and string normalization
- Base64url padding and alphabet strictness
- SQLite BLOB vs TEXT handling
- SQLite PRAGMA persistence
- SQLite foreign key activation
- SQLite driver transaction semantics
- UUID canonical validation
- Argon2id parameter mapping
- AES-GCM nonce/tag/ciphertext layout
- error taxonomy mapping
- sync vs async lifecycle differences
- file locking / close semantics
- content_type / MIME validation
- browser/sql.js exception boundaries
