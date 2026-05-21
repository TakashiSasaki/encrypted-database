# Python <-> Node.js SQLite Roundtrip Tests

These tests verify semantic interoperability between the Python and Node.js implementations of the encrypted database library.

## What it verifies
The tests create a database in one language, write an encrypted payload, and then read and verify that payload in the other language.
This guarantees that cryptographic operations (Argon2id KDF, AES-GCM, key wrapping) and SQLite schema operations are semantically equivalent across the languages.

Note that the underlying SQLite database files are **not expected to be byte-for-byte identical**. Differences in SQLite implementations, PRAGMA defaults, and internal B-Tree fragmentation can result in different bytes on disk. Payload equality and successful unlock operations are the key assertions.

These tests complement, but do not replace, the strict byte-for-byte machine-readable cryptographic test vectors found in `test-vectors/`.

## How to run
You can run the roundtrip tests by executing the shell script from the repository root:

```bash
./integration-tests/roundtrip/test_roundtrip.sh
```

## Internal details
1. **Python -> Node.js**: Creates `py_to_node.db` via Python, stores a specific deterministic JSON payload, then unlocks and asserts the payload via Node.js.
2. **Node.js -> Python**: Creates `node_to_py.db` via Node.js, stores a specific deterministic JSON payload, then unlocks and asserts the payload via Python.

Both processes use temporary database files that are cleaned up after execution.
