# Zig Component

Zig currently provides a smoke test and an initial read-only Storage Format V1 validation scaffold. It is not a production storage library and does not provide a public storage API.

## Commands

Run the smoke test (prints `vault zig smoke test ok`):
```bash
zig build run
```

Run unit tests:
```bash
zig build test
```

Validate an existing SQLite V1 database file:
```bash
zig build run -- validate <path-to-sqlite-v1-db>
```
