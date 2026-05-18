# Tips for Coding Agents

- The repository uses a monorepo setup for multi-language implementations of an encrypted database library.
- Python implementation: Found under `python/`. Uses `cryptography` for crypto ops. Make sure to run `pip install -e .[test]` and run tests using `pytest tests/`.
- Node.js implementation: Found under `nodejs/`. Uses `better-sqlite3`, native `crypto` module, and `argon2`. Test with `npm test` via Jest. Due to ESM vs CJS support in `uuid`, we are using `uuid@9.0.1` for CommonJS compatibility in tests.
- Shared SQL Schema: Handled from `docs/backend/sqlite/schema.sql`. Note that using `cross_platform` is strictly prohibited by ADR-0003; all tests must use concrete platforms such as `linux`.
- When using SQLite as the backend, the Node.js and Python implementations must be able to use the exact same SQLite database.
- When generating Argon2id parameters, always refer to `docs/providers/passphrase-argon2id.md` for the correct parameters (Time Cost 3, Memory 256MB, Parallelism 4).
- The JSON recorded in the database and the JSON before encryption must always be JCS (RFC 8785) normalized. Both the Python and Node.js implementations must strictly enforce JCS normalization. If an existing JCS normalization library is not fully compliant with the RFC, a custom JCS normalization library must be implemented and verified against all official test vectors before it is used.
