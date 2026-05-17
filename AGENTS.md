# Tips for Coding Agents

- The repository uses a monorepo setup for multi-language implementations of an encrypted database library.
- Python implementation: Found under `python/`. Uses `cryptography` for crypto ops. Make sure to run `pip install -e .[test]` and run tests using `pytest tests/`.
- Node.js implementation: Found under `nodejs/`. Uses `better-sqlite3`, native `crypto` module, and `argon2`. Test with `npm test` via Jest. Due to ESM vs CJS support in `uuid`, we are using `uuid@9.0.1` for CommonJS compatibility in tests.
- Shared SQL Schema: Handled from `docs/schema.sql`. Note that we added a `cross_platform` fallback in the schema tables (`platform_tbl`, `unlock_provider_platform_tbl`) so unit tests running on OS-agnostic testing containers wouldn't fail foreign key checks.
- When generating Argon2id parameters, always refer to `docs/argon2id_defaults.md` for the correct parameters (Time Cost 3, Memory 256MB, Parallelism 4).
