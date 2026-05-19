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

    test('unlockDatabase fails on unsupported platform', async () => {
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
        aadPolicy.getPolicy = jest.fn().mockImplementation((name) => {
            throw new Error('Other Error');
        });

        await expect(storage.unlockDatabase('my_secure_password')).rejects.toThrow('Other Error');

        aadPolicy.getPolicy = originalGetPolicy;
    });

    test('initializeDatabase fails on unknown platform', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await expect(storage.initializeDatabase('pass', 'unknown_os')).rejects.toThrow(errors.UnsupportedPlatform);
    });

    test('storePayload fails when database is locked', () => {
        const storage = new EncryptedStorage(tempDbPath);
        expect(() => storage.storePayload('id', 'type', {})).toThrow(errors.StorageLocked);
    });

    test('retrievePayload fails when database is locked', () => {
        const storage = new EncryptedStorage(tempDbPath);
        expect(() => storage.retrievePayload('id')).toThrow(errors.StorageLocked);
    });

    test('retrievePayload fails if object not found', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('pass', 'linux');
        expect(() => storage.retrievePayload('00000000-0000-0000-0000-000000000000')).toThrow(errors.ObjectNotFound);
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

    test('unlockDatabase fails if no active db kek', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        // Create an empty db, without calling initializeDatabase
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.StorageNotInitialized);
    });
});
