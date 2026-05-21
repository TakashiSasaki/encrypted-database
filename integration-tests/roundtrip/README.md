# Cross-Language SQLite Roundtrip Integration Tests

These tests prove semantic cross-language interoperability between the Python and Node.js backend implementations.
Because SQLite stores file formats similarly across standard bindings and environments, we can prove that a `.db` file created by one language's implementation can be flawlessly unlocked and read by the other language implementation.

**These tests assert semantic interoperability, not byte-for-byte exactness of the `.db` artifacts.**

## Running the Tests

To run the integration tests locally, just execute:

```bash
cd integration-tests/roundtrip
npm install
./test_roundtrip.sh
```

## What it tests:
1. Python creates a database file.
2. Python `initialize_database` writes key materials.
3. Python encrypts and stores a JSON payload object.
4. Python outputs the `objectUuid`.
5. Node.js opens that exact same SQLite file.
6. Node.js successfully unlocks the database using the same passphrase.
7. Node.js retrieves and decrypts the object matching the output `objectUuid`.
8. The payload contents exactly match what Python initially encrypted.
9. This exact process is then repeated in reverse (Node.js creates -> Python reads).
