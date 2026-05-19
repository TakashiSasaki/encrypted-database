const fs = require('fs');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');

describe('Storage Lifecycle', () => {
    let dbPath = 'test_lifecycle.db';

    beforeEach(() => {
        try { fs.unlinkSync(dbPath); } catch (e) {}
    });

    afterEach(() => {
        try { fs.unlinkSync(dbPath); } catch (e) {}
    });

    test('lifecycle states track properly', async () => {
        const storage = new EncryptedStorage(dbPath);

        // 1. Uninitialized
        expect(storage.getStatus()).toBe('uninitialized');
        expect(storage.isUnlocked()).toBe(false);
        expect(storage.isClosed()).toBe(false);

        // 2. Lock should not throw on initialized or uninitialized, as long as not closed
        storage.lock();

        // 3. Store should fail
        expect(() => storage.storePayload('schema', 'type', {})).toThrow(errors.StorageLocked);

        // 4. Initialize
        await storage.initializeDatabase('pass', 'linux');
        expect(storage.getStatus()).toBe('open_unlocked');
        expect(storage.isUnlocked()).toBe(true);

        // 5. Lock
        storage.lock();
        expect(storage.getStatus()).toBe('open_locked');
        expect(storage.isUnlocked()).toBe(false);

        // 6. Unlock
        await storage.unlockDatabase('pass');
        expect(storage.getStatus()).toBe('open_unlocked');

        // 7. Close
        storage.close();
        expect(storage.getStatus()).toBe('closed');
        expect(storage.isClosed()).toBe(true);
        expect(storage.isUnlocked()).toBe(false);

        // 8. Close is idempotent
        storage.close();

        // 9. Operations fail on close
        expect(() => storage.lock()).toThrow(errors.StorageClosed);
        await expect(storage.initializeDatabase('pass', 'linux')).rejects.toThrow(errors.StorageClosed);
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.StorageClosed);
    });
});
