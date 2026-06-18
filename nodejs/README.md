# Node.js Encrypted Storage

This library provides the Node.js implementation of the Encrypted Database, an application-layer encryption and key management solution.

**Status:** `baseline-public`. Storage Format V1 is stable.

## Features
- Manages encryption key hierarchies (`unlock_kek` -> `database_kek` -> `record_dek`).
- Encrypts payloads using AES-256-GCM.
- Follows RFC 8785 JSON Canonicalization Scheme (JCS) for AAD generation.
- Stores metadata using `better-sqlite3` and the standard schema (`docs/backend/sqlite/schema.sql`).

## Installation
**Note:** Python and Node.js are `baseline-public` certified. Packages are not yet published to npm. A local/monorepo install remains available. Actual publication status must not be overclaimed.

To install the module locally from the repository, ensure you are in the `nodejs` directory and install dependencies:
```bash
npm install
```

## Running Tests
Tests are written using Jest.
```bash
cd nodejs
npm test
```

## Package Entrypoint
The package root cleanly exports the public API classes and errors.

```javascript
const { EncryptedStorage, ObjectNotFound, StorageLocked } = require('encrypted-storage');
// Or using relative path if working locally:
// const { EncryptedStorage, ObjectNotFound } = require('.');
```

## Basic Usage

### Lifecycle: Initialize, Unlock, Lock, Close

```javascript
const { EncryptedStorage } = require('encrypted-storage');

async function run() {
    // Initialize database
    const storage = new EncryptedStorage('my_database.sqlite');
    await storage.initializeDatabase('my_super_secret_password', 'linux');

    // Or open and unlock an existing database
    const storageExisting = new EncryptedStorage('my_database.sqlite');
    await storageExisting.unlockDatabase('my_super_secret_password');

    // Lock the database (purges KEKs from memory)
    storage.lock();

    // Close connection
    storage.close();
}

run();
```

### Payload Operations: Store, Retrieve, Update, Delete

```javascript
const { EncryptedStorage } = require('encrypted-storage');

async function runOps() {
    const storage = new EncryptedStorage('my_database.sqlite');
    await storage.unlockDatabase('my_super_secret_password');

    const schemaUuid = '00000000-0000-4000-8000-000000000001';

    // Store payload
    const payload = { secret: 'data', value: 42 };
    const objectUuid = storage.storePayload(schemaUuid, 'application/json', payload);

    // Retrieve payload
    const retrieved = storage.retrievePayload(objectUuid);
    console.log(retrieved);

    // Update payload
    const newPayload = { secret: 'data-updated', value: 99 };
    storage.updatePayload(objectUuid, schemaUuid, 'application/json', newPayload);

    // Delete payload
    storage.deletePayload(objectUuid);

    storage.close();
}

runOps();
```

## Error Model
The library provides named exception classes mapped across Python and Node.js implementations.

```javascript
const { EncryptedStorage, ObjectNotFound } = require('encrypted-storage');

async function checkError() {
    const storage = new EncryptedStorage('my_database.sqlite');
    await storage.unlockDatabase('my_super_secret_password');

    try {
        const retrieved = storage.retrievePayload("00000000-0000-4000-8000-000000000002");
    } catch (e) {
        if (e instanceof ObjectNotFound) {
            console.log("Payload not found.");
        }
    }
}

checkError();
```

## Metadata Notes
The `created_by_version` field in database metadata is diagnostic provenance metadata and is not a compatibility gate across readers/writers.



See also: [`docs/implementation-notes/api-parity-matrix.md`](../docs/implementation-notes/api-parity-matrix.md)
