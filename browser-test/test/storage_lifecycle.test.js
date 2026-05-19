const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');

describe('Storage Lifecycle Browser', () => {

    test('lifecycle states track properly', async () => {
        const storage = new EncryptedStorage();

        // 1. closed before init
        expect(storage.getStatus()).toBe('closed');
        expect(storage.isClosed()).toBe(true);
        expect(storage.isUnlocked()).toBe(false);

        await storage.init();

        // 2. uninitialized after init
        expect(storage.getStatus()).toBe('uninitialized');
        expect(storage.isUnlocked()).toBe(false);
        expect(storage.isClosed()).toBe(false);

        // 3. Lock should not throw on initialized or uninitialized, as long as not closed
        storage.lock();

        // 4. Store should fail
        expect(() => storage.storePayload('schema', 'type', {})).toThrow(errors.StorageLocked);

        // 5. Initialize
        await storage.initializeDatabase('pass', 'web');
        expect(storage.getStatus()).toBe('open_unlocked');
        expect(storage.isUnlocked()).toBe(true);

        // 6. Lock
        storage.lock();
        expect(storage.getStatus()).toBe('open_locked');
        expect(storage.isUnlocked()).toBe(false);

        // 7. Unlock
        await storage.unlockDatabase('pass');
        expect(storage.getStatus()).toBe('open_unlocked');

        // 8. Close
        storage.close();
        expect(storage.getStatus()).toBe('closed');
        expect(storage.isClosed()).toBe(true);
        expect(storage.isUnlocked()).toBe(false);

        // 9. Close is idempotent
        storage.close();

        // 10. Operations fail on close
        expect(() => storage.lock()).toThrow(errors.StorageClosed);
        await expect(storage.initializeDatabase('pass', 'web')).rejects.toThrow(errors.StorageClosed);
        await expect(storage.unlockDatabase('pass')).rejects.toThrow(errors.StorageClosed);
    });
});
