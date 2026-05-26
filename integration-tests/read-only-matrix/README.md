# Read-Only Interoperability Matrix

This directory contains the read-only fixture interoperability tests, ensuring that SQLite databases created by the full library implementations (Python, Node.js) can be correctly read and decrypted by the portability scaffold read-only implementations (Go, Rust).

## How it works

The shell script `test_readonly_matrix.sh` coordinates the following workflow:

1. **Generation:** It invokes generator scripts (`generate_fixture_python.py`, `generate_fixture_node.js`). These scripts use the existing mature `EncryptedStorage` APIs to:
   - Create a new temporary SQLite DB using Storage Format V1 in a temporary directory (which is cleaned up on exit).
   - Initialize it with a test passphrase.
   - Store a test JSON payload.
   - Output the connection details (DB path, passphrase, object UUID, and the expected payload as **JCS canonical payload bytes in lowercase hex**) to an environment file.

*(Note: This harness is strictly for read-only decrypt interoperability verification. It does not validate or represent writer/database creation APIs for Go/Rust, which remain unimplemented.)*

2. **Execution:** The script sources the environment file, which sets the following variables:
   - `VAULT_SQLITE_V1_FIXTURE_DB`
   - `VAULT_SQLITE_V1_FIXTURE_PASSPHRASE`
   - `VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID`
   - `VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX`

3. **Validation:** It then invokes the Go (`go test`) and Rust (`cargo test`) test suites. The `ExternalFixture` tests in Go and Rust detect these environment variables, open the specified database as read-only, decrypt the payload, and assert that the resulting bytes match the expected hex string.

## Running the tests

You can execute the entire matrix test by running from the directory:

```bash
./test_readonly_matrix.sh
```

Or from the repository root:

```bash
./integration-tests/read-only-matrix/test_readonly_matrix.sh
```

### Important Notes on Execution
- The shell script will run `pip install -e .[test]` and `npm ci` for the Python and Node.js dependencies, which **may take some time** depending on your environment.
- **Manual CI execution:** You can run this matrix on GitHub Actions by manually triggering the **Read-only Matrix** workflow via `workflow_dispatch`. It is **not yet automatic on push or pull_request** to avoid increasing CI runtime for all changes.
- This harness tests **read-only decrypt interoperability only**. Go/Rust writer APIs, database creation APIs, and the full read/write roundtrip matrix are still future work.
- If you wish to run the Go or Rust tests manually against an existing fixture, you must export the following environment variables. The values must match the generated database connection details:
  - `VAULT_SQLITE_V1_FIXTURE_DB`: The path to the database.
  - `VAULT_SQLITE_V1_FIXTURE_PASSPHRASE`: The string passphrase.
  - `VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID`: The UUID of the object.
  - `VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX`: The lowercase hex string of the JCS canonical payload bytes.
