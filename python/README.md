# Python Encrypted Storage

This library provides the Python implementation of the Encrypted Database, an application-layer encryption and key management solution.

**Status:** `baseline-public`. Storage Format V1 is stable.

## Features
- Manages encryption key hierarchies (`unlock_kek` -> `database_kek` -> `record_dek`).
- Encrypts payloads using AES-256-GCM.
- Follows RFC 8785 JSON Canonicalization Scheme (JCS) for AAD generation.
- Stores metadata using SQLite (`docs/backend/sqlite/schema.sql`).

## Installation
**Note:** Python and Node.js are baseline-public certified. Distribution/publication may still be manual or pending; actual PyPI publication is not yet done, and release automation does not yet exist.

To install the module locally from the repository:
```bash
pip install .
```

## Running Tests
Tests are written using `pytest`.
```bash
cd python
pip install -e .[test]
pytest --cov=src
```

## Package Entrypoint
The package root cleanly exposes the public API classes and errors.

```python
from encrypted_storage import EncryptedStorage
from encrypted_storage import ObjectNotFound, StorageLocked
```

## Basic Usage

### Lifecycle: Initialize, Unlock, Lock, Close

```python
from encrypted_storage import EncryptedStorage

# Initialize database
storage = EncryptedStorage("my_database.sqlite")
storage.initialize_database("my_super_secret_password", "linux")

# Or open and unlock an existing database
storage = EncryptedStorage("my_database.sqlite")
storage.unlock_database("my_super_secret_password")

# Lock the database (purges KEKs from memory)
storage.lock()

# Close connection
storage.close()
```

### Payload Operations: Store, Retrieve, Update, Delete

```python
from encrypted_storage import EncryptedStorage

storage = EncryptedStorage("my_database.sqlite")
storage.unlock_database("my_super_secret_password")

schema_uuid = "00000000-0000-4000-8000-000000000001"

# Store payload
payload = {"secret": "data", "value": 42}
object_uuid = storage.store_payload(schema_uuid, "application/json", payload)

# Retrieve payload
retrieved = storage.retrieve_payload(object_uuid)
print(retrieved)

# Update payload
new_payload = {"secret": "data-updated", "value": 99}
storage.update_payload(object_uuid, schema_uuid, "application/json", new_payload)

# Delete payload
storage.delete_payload(object_uuid)
```

## Error Model
The library provides named exception classes mapped across Python and Node.js implementations.

```python
from encrypted_storage import EncryptedStorage, ObjectNotFound

storage = EncryptedStorage("my_database.sqlite")
storage.unlock_database("my_super_secret_password")

try:
    retrieved = storage.retrieve_payload("00000000-0000-4000-8000-000000000002")
except ObjectNotFound:
    print("Payload not found.")
```

## Metadata Notes
The `created_by_version` field in database metadata is diagnostic provenance metadata and is not a compatibility gate across readers/writers.



See also: [`docs/implementation-notes/api-parity-matrix.md`](../docs/implementation-notes/api-parity-matrix.md)
