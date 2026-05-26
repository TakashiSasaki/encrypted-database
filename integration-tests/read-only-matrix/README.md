# Read-Only Interoperability Matrix

This directory contains the read-only fixture interoperability tests, ensuring that SQLite databases created by the full library implementations (Python, Node.js) can be correctly read and decrypted by the portability scaffold read-only implementations (Go, Rust).

## How it works

The shell script `test_readonly_matrix.sh` coordinates the following workflow:

1. **Generation:** It invokes generator scripts (`generate_fixture_python.py`, `generate_fixture_node.js`). These scripts use the existing mature `EncryptedStorage` APIs to:
   - Create a new temporary SQLite DB using Storage Format V1.
   - Initialize it with a test passphrase.
   - Store a test JSON payload.
   - Output the connection details (DB path, passphrase, object UUID, and the expected JCS canonical payload hex) to an environment file.

2. **Execution:** The script sources the environment file, which sets the following variables:
   - `VAULT_SQLITE_V1_FIXTURE_DB`
   - `VAULT_SQLITE_V1_FIXTURE_PASSPHRASE`
   - `VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID`
   - `VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX`

3. **Validation:** It then invokes the Go (`go test`) and Rust (`cargo test`) test suites. The `ExternalFixture` tests in Go and Rust detect these environment variables, open the specified database as read-only, decrypt the payload, and assert that the resulting bytes match the expected hex string.

## Running the tests

You can execute the entire matrix test by running:

```bash
./test_readonly_matrix.sh
```

*(You may need to run from the repository root as `integration-tests/read-only-matrix/test_readonly_matrix.sh` depending on your current directory).*
