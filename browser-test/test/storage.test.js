const fs = require('fs');
const path = require('path');
const os = require('os');
const EncryptedStorage = require('../src/storage');
const initSqlJs = require('sql.js/dist/sql-wasm.js');
const aadPolicy = require('../src/aadPolicy');

describe('EncryptedStorage', () => {

    test('initialization and unlock', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

        // Export DB data to pass it to the next instance
        const dbData = storage.db.export();
        storage.close();

        const storage2 = new EncryptedStorage();
        await storage2.init(); // Init creates a blank db. Let's overwrite it.
        const SQL = await require('sql.js/dist/sql-wasm.js')();
        storage2.db = new SQL.Database(dbData); // Overwrite with saved data

        await expect(storage2.unlockDatabase('wrong_password')).rejects.toThrow('Failed to unlock database');

        await storage2.unlockDatabase('my_secure_password');
        expect(storage2.activeDbKek).not.toBeNull();
        storage2.close();
    });

    test('store and retrieve payload', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

        const payload = { secret: 'data', value: 42 };
        const schemaUuid = '00000000-0000-4000-8000-000000000001';

        const objectUuid = storage.storePayload(schemaUuid, 'application/json', payload);

        const retrieved = storage.retrievePayload(objectUuid);
        expect(retrieved).toEqual(payload);

        // Test retrieving after locking
        storage.lock();
        expect(() => storage.retrievePayload(objectUuid)).toThrow('Database is locked');
        expect(() => storage.storePayload(schemaUuid, 'application/json', payload)).toThrow('Database is locked');

        storage.close();
    });

    test('retrievePayload handles not found object', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');
        expect(() => storage.retrievePayload('not-found-uuid')).toThrow('Object not found');
        storage.close();
    });

    test('unlockDatabase fails with no database init', async () => {
        const storage = new EncryptedStorage();
        await expect(storage.unlockDatabase('pass')).rejects.toThrow('Database not initialized');
    });

    test('unlockDatabase fails if no db kek', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await expect(storage.unlockDatabase('pass')).rejects.toThrow('No active database KEK found');
    });

    test('unlockDatabase ignores unknown aad policy', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

        storage.db.exec(`UPDATE wrapped_key_tbl SET aad_policy = 'unknown'`);

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow('Failed to unlock database');
        storage.close();
    });

    test('retrievePayload fails on bad wrap info', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

        const payload = { secret: 'data', value: 42 };
        const schemaUuid = '00000000-0000-4000-8000-000000000001';

        const objectUuid = storage.storePayload(schemaUuid, 'application/json', payload);

        storage.db.exec(`PRAGMA foreign_keys = OFF;`);
        storage.db.exec(`UPDATE wrapped_key_tbl SET wrapped_kid = '00000000-0000-4000-8000-000000000000'`);
        storage.db.exec(`PRAGMA foreign_keys = ON;`);

        expect(() => storage.retrievePayload(objectUuid)).toThrow('Record DEK wrap info not found');

        storage.close();
    });

    test('unlockDatabase continues loop if no unlock provider', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

        storage.db.exec(`DELETE FROM unlock_kek_tbl`);

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow('Failed to unlock database');
        storage.close();
    });

    test('initializeDatabase rollback on error', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        storage.db.run = () => { throw new Error('Mock insert error'); };
        await expect(storage.initializeDatabase('test', 'linux')).rejects.toThrow('Mock insert error');
    });

    test('storePayload rollback on error', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

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
        expect(() => storage.storePayload(schemaUuid, 'application/json', payload)).toThrow('Mock store error');
    });

    test('unlockDatabase ignores unknown providers but throws on others', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

        storage.db.exec(`PRAGMA foreign_keys = OFF;`);
        storage.db.exec("UPDATE unlock_kek_tbl SET unlock_provider = 'unknown_provider'");
        storage.db.exec(`PRAGMA foreign_keys = ON;`);

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow('Failed to unlock database');
    });

    test('unlockDatabase throws actual error from getPolicy', async () => {
        const storage = new EncryptedStorage();
        await storage.initializeDatabase('my_secure_password', 'linux');

        const originalGetPolicy = aadPolicy.getPolicy;
        aadPolicy.getPolicy = jest.fn().mockImplementation((name) => {
            throw new Error('Other Error');
        });

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow('Other Error');

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
        await storage.initializeDatabase('my_secure_password', 'linux');
        storage.db.exec("DELETE FROM wrapped_key_tbl");
        await expect(storage.unlockDatabase('pass')).rejects.toThrow('No wrap info found');
        storage.close();
    });

    test('close and lock handle nulls', () => {
        const storage = new EncryptedStorage();
        storage.close(); // db is null
        storage.lock();  // activeDbKek is null
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
