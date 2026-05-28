# Python Encrypted Storage

This library provides the Python implementation of the Encrypted Database, an application-layer encryption and key management solution.

## Features
- Manages encryption key hierarchies (`unlock_kek` -> `database_kek` -> `record_dek`).
- Encrypts payloads using AES-256-GCM.
- Follows RFC 8785 JSON Canonicalization Scheme (JCS) for AAD generation.
- Stores metadata using SQLite (`docs/backend/sqlite/schema.sql`).

## Installation
You can install this module and its dependencies using pip:
```bash
cd python
pip install -e .
```

## Running Tests
Tests are written using `pytest`.
```bash
cd python
pip install -e .[test]
pytest --cov=src
```

## Basic Usage

```python
from encrypted_storage.storage import EncryptedStorage

# Initialize database
storage = EncryptedStorage("my_database.sqlite")
storage.initialize_database("my_super_secret_password", "linux")

# Store payload
schema_uuid = "00000000-0000-4000-8000-000000000001"
payload = {"secret": "data", "value": 42}
object_uuid = storage.store_payload(schema_uuid, "application/json", payload)

# Retrieve payload
retrieved = storage.retrieve_payload(object_uuid)
print(retrieved)
```


See also: [`docs/implementation-notes/api-parity-matrix.md`](../docs/implementation-notes/api-parity-matrix.md)
