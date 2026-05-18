# Node.js Encrypted Storage

This library provides the Node.js implementation of the Encrypted Database, an application-layer encryption and key management solution.

## Features
- Manages encryption key hierarchies (`unlock_kek` -> `database_kek` -> `record_dek`).
- Encrypts payloads using AES-256-GCM.
- Follows RFC 8785 JSON Canonicalization Scheme (JCS) for AAD generation.
- Stores metadata using `better-sqlite3` and the standard schema (`docs/backend/sqlite/schema.sql`).

## Installation
Ensure you are in the `nodejs` directory and install dependencies:
```bash
cd nodejs
npm install
```

## Running Tests
Tests are written using Jest.
```bash
cd nodejs
npm test
```

## Basic Usage

```javascript
const EncryptedStorage = require('./src/storage');

async function run() {
    // Initialize database
    const storage = new EncryptedStorage('my_database.sqlite');
    await storage.initializeDatabase('my_super_secret_password', 'linux');

    // Store payload
    const schemaUuid = '00000000-0000-4000-8000-000000000001';
    const payload = { secret: 'data', value: 42 };
    const objectUuid = storage.storePayload(schemaUuid, 'application/json', payload);

    // Retrieve payload
    const retrieved = storage.retrievePayload(objectUuid);
    console.log(retrieved);
}

run();
```
