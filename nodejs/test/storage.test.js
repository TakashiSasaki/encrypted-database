const fs = require('fs');
const path = require('path');
const os = require('os');
const EncryptedStorage = require('../src/storage');

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
        await storage.initializeDatabase('my_secure_password');
        storage.close();

        const storage2 = new EncryptedStorage(tempDbPath);
        await expect(storage2.unlockDatabase('wrong_password')).rejects.toThrow('Failed to unlock database');

        await storage2.unlockDatabase('my_secure_password');
        expect(storage2.activeDbKek).not.toBeNull();
        storage2.close();
    });

    test('store and retrieve payload', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('my_secure_password');

        const payload = { secret: 'data', value: 42 };
        const schemaUuid = '00000000-0000-0000-0000-000000000001';

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
});
