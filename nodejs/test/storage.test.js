const fs = require('fs');
const path = require('path');
const os = require('os');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');
const aadPolicy = require('../src/aadPolicy');

describe('EncryptedStorage', () => {
    let tempDbPath;

    beforeEach(() => {
        tempDbPath = path.join(os.tmpdir(), `test-${Date.now()}-${Math.random()}.db`);
    });

    afterEach(() => {
        if (fs.existsSync(tempDbPath)) {
            fs.unlinkSync(tempDbPath);
        }
    });

    test('initialization and unlock', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('my_secure_password', 'linux');
        storage.close();

        const storage2 = new EncryptedStorage(tempDbPath);
        await expect(storage2.unlockDatabase('wrong_password')).rejects.toThrow(errors.UnlockFailed);

        await storage2.unlockDatabase('my_secure_password');
        expect(storage2.activeDbKek).not.toBeNull();
        storage2.close();
    });

    test('writer PRAGMA profile', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('my_secure_password', 'linux');
        storage.close();

        const db = require('better-sqlite3')(tempDbPath);
        // Validate required writer-initialization PRAGMAs for new DBs
        expect(db.pragma('page_size', { simple: true })).toBe(4096);
        expect(db.pragma('auto_vacuum', { simple: true })).toBe(0);
        // Note: journal_mode=WAL and synchronous=NORMAL are recommended operational
        // PRAGMAs for file-backed environments, not strict V1 conformance invariants.
        // We do not strictly assert them here to allow environments without WAL to pass.
        db.close();
    });

    test('store and retrieve payload', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('my_secure_password', 'linux');

        const payload = { secret: 'data', value: 42 };
        const schemaUuid = '00000000-0000-4000-8000-000000000001';

        const objectUuid = storage.storePayload(schemaUuid, 'application/json', payload);

        const retrieved = storage.retrievePayload(objectUuid);
        expect(retrieved).toEqual(payload);

        storage.close();

        const storage2 = new EncryptedStorage(tempDbPath);
        await storage2.unlockDatabase('my_secure_password');
        const retrieved2 = storage2.retrievePayload(objectUuid);
        expect(retrieved2).toEqual(payload);
        storage2.close();
    });

    test('initializeDatabase fails on unsupported platform', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await expect(storage.initializeDatabase('pass', 'cross_platform')).rejects.toThrow(errors.UnsupportedPlatform);
    });

    test('unlockDatabase continues loop if aad policy error', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('my_secure_password', 'linux');

        storage.conn.exec(`UPDATE wrapped_key_tbl SET aad_policy = 'unknown'`);

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow(errors.UnlockFailed);
        storage.close();
    });

    test('unlockDatabase throws actual error from getPolicy', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('my_secure_password', 'linux');

        const originalGetPolicy = aadPolicy.getPolicy;
        class TestPolicyError extends Error {}
        aadPolicy.getPolicy = jest.fn().mockImplementation((name) => {
            throw new TestPolicyError('Other Error');
        });

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow(TestPolicyError);

        aadPolicy.getPolicy = originalGetPolicy;
    });

    test('initializeDatabase fails on unknown platform', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await expect(storage.initializeDatabase('pass', 'unknown_os')).rejects.toThrow(errors.UnsupportedPlatform);
    });

    test('updatePayload success', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');

        const payloadA = { "secret": "data", "value": 42 };
        const schemaUuidA = "00000000-0000-4000-8000-000000000001";
        const contentTypeA = "application/json";

        const objectUuid = storage.storePayload(schemaUuidA, contentTypeA, payloadA);

        const findStmt = storage.conn.prepare("SELECT created_at_ms, updated_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?");
        const rowA = findStmt.get(objectUuid);

        const payloadB = { "secret": "data-updated", "value": 99 };
        const schemaUuidB = "00000000-0000-4000-8000-000000000002";
        const contentTypeB = "application/json+updated";

        storage.updatePayload(objectUuid, schemaUuidB, contentTypeB, payloadB);

        const retrieved = storage.retrievePayload(objectUuid);
        expect(retrieved).toEqual(payloadB);

        const rowB = storage.conn.prepare("SELECT schema_uuid, content_type, created_at_ms, updated_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?").get(objectUuid);

        expect(rowB.schema_uuid).toBe(schemaUuidB);
        expect(rowB.content_type).toBe(contentTypeB);
        expect(rowB.created_at_ms).toBe(rowA.created_at_ms);
        expect(rowB.updated_at_ms).toBeGreaterThanOrEqual(rowA.updated_at_ms);

        storage.close();
    });

    test('updatePayload fails if not found', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        expect(() => storage.updatePayload('00000000-0000-4000-8000-000000000000', '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('updatePayload fails on sql error', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        storage.conn.pragma('foreign_keys = OFF');
        storage.conn.exec('DROP TABLE encrypted_object_tbl');

        expect(() => storage.updatePayload(objectUuid, '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.DatabaseBackendError);
        storage.close();
    });

    test('updatePayload fails on update sql error', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        storage.conn.exec('ALTER TABLE encrypted_object_tbl RENAME COLUMN ciphertext TO missing_col');

        expect(() => storage.updatePayload(objectUuid, '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.DatabaseBackendError);
        storage.close();
    });

    test('deletePayload success', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        storage.deletePayload(objectUuid);

        expect(() => storage.retrievePayload(objectUuid)).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('deletePayload fails if not found', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        expect(() => storage.deletePayload('00000000-0000-4000-8000-000000000000')).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('deletePayload fails on sql error', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', { a: 1 });

        storage.conn.pragma('foreign_keys = OFF');
        storage.conn.exec('DROP TABLE encrypted_object_tbl');

        expect(() => storage.deletePayload(objectUuid)).toThrow(errors.DatabaseBackendError);
        storage.close();
    });

    test('storePayload fails when database is locked', () => {
        const storage = new EncryptedStorage(tempDbPath);
        expect(() => storage.storePayload('11111111-1111-4111-8111-111111111111', 'application/json', {})).toThrow(errors.StorageLocked);
    });

    test('updatePayload fails when database is locked', () => {
        const storage = new EncryptedStorage(tempDbPath);
        expect(() => storage.updatePayload('11111111-1111-4111-8111-111111111111', '00000000-0000-4000-8000-000000000001', 'application/json', {})).toThrow(errors.StorageLocked);
    });

    test('deletePayload fails when database is locked', () => {
        const storage = new EncryptedStorage(tempDbPath);
        expect(() => storage.deletePayload('11111111-1111-4111-8111-111111111111')).toThrow(errors.StorageLocked);
    });

    test('retrievePayload fails when database is locked', () => {
        const storage = new EncryptedStorage(tempDbPath);
        expect(() => storage.retrievePayload('11111111-1111-4111-8111-111111111111')).toThrow(errors.StorageLocked);
    });

    test('retrievePayload fails if object not found', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        expect(() => storage.retrievePayload('00000000-0000-4000-8000-000000000000')).toThrow(errors.ObjectNotFound);
    });

    test('retrievePayload fails if wrap info not found', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        const objectUuid = storage.storePayload('00000000-0000-4000-8000-000000000001', 'application/json', {a: 1});
        storage.conn.pragma('foreign_keys = OFF');
        storage.conn.exec("UPDATE wrapped_key_tbl SET wrapped_kid = '00000000-0000-4000-8000-000000000000'");
        storage.conn.pragma('foreign_keys = ON');
        expect(() => storage.retrievePayload(objectUuid)).toThrow(errors.IntegrityCheckFailed);
    });

    test('unlockDatabase ignores if no unlock provider', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        storage.conn.exec("DELETE FROM unlock_kek_tbl");
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.UnlockFailed);
    });

    test('unlockDatabase fails on empty or uninitialized database', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        // Database lacks proper v1 schema and metadata, unlocking should fail early
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.InvalidStorageFormat);
    });

    test('AAD mutation causes decryption failure', async () => {
        const storage = new EncryptedStorage(tempDbPath);
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
        storage.conn.exec(`UPDATE encrypted_object_tbl SET content_type = 'text/plain' WHERE object_uuid = '${objectUuid}'`);

        // Attempt retrieve should fail due to tag mismatch
        expect(() => {
            storage.retrievePayload(objectUuid);
        }).toThrow();
    });
});

    test('initializeDatabase fails on wrong db', async () => {
        const path = require('path');
        const os = require('os');
        const tempDbPath = path.join(os.tmpdir(), `test-${Date.now()}-${Math.random()}.db`);
        const db = require('better-sqlite3')(tempDbPath);
        db.exec("CREATE TABLE random_tbl (id INTEGER)");
        db.close();

        const storage = new EncryptedStorage(tempDbPath);
        await expect(storage.initializeDatabase('pass', 'linux')).rejects.toThrow(errors.InvalidStorageFormat);
    });


describe('WAL Fallback', () => {
    test('should fallback gracefully when WAL or synchronous pragmas fail', () => {
        const Database = require('better-sqlite3');
        const originalPragma = Database.prototype.pragma;
        Database.prototype.pragma = function(source, options) {
            if (typeof source === 'string' && source.includes('journal_mode = WAL')) {
                throw new Error("WAL not supported test");
            }
            if (typeof source === 'string' && source.includes('synchronous = NORMAL')) {
                throw new Error("synchronous NORMAL not supported test");
            }
            return originalPragma.call(this, source, options);
        };

        try {
            const path = require('path');
            const os = require('os');
            const dbPath = path.join(os.tmpdir(), `wal-fallback-${Date.now()}-${Math.random()}.db`);
            const EncryptedStorage = require('../src/storage');
            const storage = new EncryptedStorage(dbPath);
            storage.close();
        } finally {
            Database.prototype.pragma = originalPragma;
        }
    });
});
