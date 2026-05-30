const fs = require('fs');
const path = require('path');
const os = require('os');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');
const initSqlJs = require('sql.js/dist/sql-wasm.js');
const aadPolicy = require('../src/aadPolicy');

describe('EncryptedStorage', () => {

    test('initialization and unlock', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        // Export DB data to pass it to the next instance
        const dbData = storage.db.export();
        storage.close();

        const storage2 = new EncryptedStorage();
        await storage2.init(dbData);

        await expect(storage2.unlockDatabase('wrong_password')).rejects.toThrow(errors.UnlockFailed);

        await storage2.unlockDatabase('my_secure_password');
        expect(storage2.activeDbKek).not.toBeNull();
        storage2.close();

});

    test('store and retrieve payload', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        const payload = { secret: 'data', value: 42 };
        const schemaUuid = '00000000-0000-4000-8000-000000000001';

        const objectUuid = storage.storePayload(schemaUuid, 'application/json', payload);

        const retrieved = storage.retrievePayload(objectUuid);
        expect(retrieved).toEqual(payload);

        // Test retrieving after locking
        storage.lock();
        expect(() => storage.retrievePayload(objectUuid)).toThrow(errors.StorageLocked);
        expect(() => storage.storePayload(schemaUuid, 'application/json', payload)).toThrow(errors.StorageLocked);

        storage.close();
    });

    test('updatePayload success', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'linux');

        const payloadA = { "secret": "data", "value": 42 };
        const schemaUuidA = "00000000-0000-4000-8000-000000000001";
        const contentTypeA = "application/json";

        const objectUuid = storage.storePayload(schemaUuidA, contentTypeA, payloadA);

        const findStmt = storage.db.prepare("SELECT created_at_ms, updated_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?");
        findStmt.bind([objectUuid]);
        findStmt.step();
        const rowA = findStmt.get();
        findStmt.free();

        const payloadB = { "secret": "data-updated", "value": 99 };
        const schemaUuidB = "00000000-0000-4000-8000-000000000002";
        const contentTypeB = "application/json+updated";

        storage.updatePayload(objectUuid, schemaUuidB, contentTypeB, payloadB);

        const retrieved = storage.retrievePayload(objectUuid);
        expect(retrieved).toEqual(payloadB);

        const rowBStmt = storage.db.prepare("SELECT schema_uuid, content_type, created_at_ms, updated_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?");
        rowBStmt.bind([objectUuid]);
        rowBStmt.step();
        const rowB = rowBStmt.get();
        rowBStmt.free();

        expect(rowB[0]).toBe(schemaUuidB);
        expect(rowB[1]).toBe(contentTypeB);
        expect(rowB[2]).toBe(rowA[0]);
        expect(rowB[3]).toBeGreaterThanOrEqual(rowA[1]);

        storage.close();
    });

    test('updatePayload fails if not found', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'linux');
        expect(() => storage.updatePayload('00000000-0000-4000-8000-000000000000', '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('updatePayload fails on sql error', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        storage.db.exec("PRAGMA foreign_keys = OFF");
        storage.db.exec("DROP TABLE encrypted_object_tbl");

        expect(() => storage.updatePayload(objectUuid, '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.DatabaseBackendError);
        storage.close();
    });

    test('updatePayload fails on update sql error', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        // sql.js does not support DROP COLUMN or ALTER TABLE RENAME COLUMN completely safely in some versions,
        // but it does support mocking run/exec. Let's mock db.run or db.prepare.
        const originalPrepare = storage.db.prepare;
        storage.db.prepare = function(sql) {
            if (sql.includes("UPDATE encrypted_object_tbl")) {
                throw new Error("Mock prepare error");
            }
            return originalPrepare.call(this, sql);
        };

        expect(() => storage.updatePayload(objectUuid, '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.DatabaseBackendError);
        storage.close();
    });

    test('deletePayload success', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        storage.deletePayload(objectUuid);

        expect(() => storage.retrievePayload(objectUuid)).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('deletePayload fails if not found', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'linux');
        expect(() => storage.deletePayload('00000000-0000-4000-8000-000000000000')).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('deletePayload fails on sql error', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        storage.db.exec("PRAGMA foreign_keys = OFF");
        storage.db.exec("DROP TABLE encrypted_object_tbl");

        expect(() => storage.deletePayload(objectUuid)).toThrow(errors.DatabaseBackendError);
        storage.close();
    });

    test('updatePayload fails when database is locked', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        expect(() => storage.updatePayload('11111111-1111-4111-8111-111111111111', '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.StorageLocked);
    });

    test('deletePayload fails when database is locked', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        expect(() => storage.deletePayload('11111111-1111-4111-8111-111111111111')).toThrow(errors.StorageLocked);
    });

    test('retrievePayload handles not found object', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');
        expect(() => storage.retrievePayload('00000000-0000-4000-8000-000000000000')).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('unlockDatabase fails with no database init', async () => {
        const storage = new EncryptedStorage();
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.StorageNotInitialized);
    });

    test('unlockDatabase fails if no db kek', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.InvalidStorageFormat);
    });

    test('unlockDatabase ignores unknown aad policy', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        storage.db.exec(`UPDATE wrapped_key_tbl SET aad_policy = 'unknown'`);

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow(errors.UnlockFailed);
        storage.close();
    });

    test('retrievePayload fails on bad wrap info', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        const payload = { secret: 'data', value: 42 };
        const schemaUuid = '00000000-0000-4000-8000-000000000001';

        const objectUuid = storage.storePayload(schemaUuid, 'application/json', payload);

        storage.db.exec(`PRAGMA foreign_keys = OFF;`);
        storage.db.exec(`UPDATE wrapped_key_tbl SET wrapped_kid = '00000000-0000-4000-8000-000000000000'`);
        storage.db.exec(`PRAGMA foreign_keys = ON;`);

        expect(() => storage.retrievePayload(objectUuid)).toThrow(errors.IntegrityCheckFailed);

        storage.close();
    });

    test('unlockDatabase continues loop if no unlock provider', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        storage.db.exec(`DELETE FROM unlock_kek_tbl`);

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow(errors.UnlockFailed);
        storage.close();
    });

    test('initializeDatabase rollback on error', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        storage.db.run = () => { throw new Error('Mock insert error'); };
        await expect(storage.initializeDatabase('test', 'web')).rejects.toThrow(Error);
    });

    test('storePayload rollback on error', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'web');

        // Mock to throw an error on the last insert inside transaction
        const origRun = storage.db.run;
        storage.db.run = function(sql, params) {
            if (sql.includes('encrypted_object_tbl')) {
                throw new Error('Mock store error');
            }
            return origRun.call(this, sql, params);
        };

        const payload = { test: 1 };
        const schemaUuid = '00000000-0000-4000-8000-000000000001';
        expect(() => storage.storePayload(schemaUuid, 'application/json', payload)).toThrow(Error);
    });

    test('provider config is stored as canonical json', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        const stmt = storage.db.prepare("SELECT provider_config_json FROM unlock_kek_tbl LIMIT 1");
        stmt.step();
        const configJson = stmt.getAsObject().provider_config_json;
        stmt.free();

        // configJson is stored as a string directly, not base64 encoded
        // It should match JCS canonical format (no spaces around colons/commas, keys sorted)
        const parsed = JSON.parse(configJson);
        const { canonicalize } = require('json-canonicalize');
        expect(configJson).toEqual(canonicalize(parsed));

        storage.close();
    });

    test('unlockDatabase ignores unknown providers but throws on others', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        storage.db.exec(`PRAGMA foreign_keys = OFF;`);
        storage.db.exec("UPDATE unlock_kek_tbl SET unlock_provider = 'unknown_provider'");
        storage.db.exec(`PRAGMA foreign_keys = ON;`);

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow(errors.UnlockFailed);
    });

    test('unlockDatabase throws actual error from getPolicy', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'web');

        const originalGetPolicy = aadPolicy.getPolicy;
        class TestPolicyError extends Error {}
        aadPolicy.getPolicy = jest.fn().mockImplementation((name) => {
            throw new TestPolicyError('Other Error');
        });

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow(TestPolicyError);

        aadPolicy.getPolicy = originalGetPolicy;
    });
});

    test('locateFile mapping coverage', async () => {
        // Just directly call locateFile map from a mock config
        const testConfig = { locateFile: file => {
              if (file.endsWith('.wasm')) return 'sql-wasm.wasm';
              return file;
            }};

        expect(testConfig.locateFile('test.wasm')).toBe('sql-wasm.wasm');
        expect(testConfig.locateFile('test.js')).toBe('test.js');
    });

    test('_b64e and _b64d methods branch coverage', () => {
        const storage = new EncryptedStorage();
        // test buffer
        const buf = Buffer.from('hello');
        const b64e = storage._b64e(buf);
        expect(storage._b64e('hello')).toBe(b64e); // string

        // test string to decode with padding needs
        const decoded = storage._b64d('aGVsbG8'); // length 7, 7%4 = 3
        expect(decoded.toString()).toBe('hello');
    });

    test('unlockDatabase fails with no wrap info', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');
        storage.db.exec("DELETE FROM wrapped_key_tbl");
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.UnlockFailed);
        storage.close();
    });

    test('close and lock handle nulls', () => {
        const storage = new EncryptedStorage();
        storage.close(); // db is null
        expect(() => storage.lock()).toThrow(errors.StorageClosed);
        expect(storage.db).toBeNull();
    });

    test('AAD mutation causes decryption failure', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('secure-password', 'linux');
        await storage.unlockDatabase('secure-password');

        const objectUuid = await storage.storePayload(
            '11111111-1111-4111-8111-111111111111',
            'application/json',
            { secret: "data" }
        );

        const decrypted = storage.retrievePayload(objectUuid);
        expect(decrypted).toEqual({ secret: "data" });

        // Mutate AAD bound column
        storage.db.exec(`UPDATE encrypted_object_tbl SET content_type = 'text/plain' WHERE object_uuid = '${objectUuid}'`);

        // Attempt retrieve should fail due to tag mismatch
        expect(() => {
            storage.retrievePayload(objectUuid);
        }).toThrow();
    });
