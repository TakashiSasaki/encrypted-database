const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');

describe('Storage Lifecycle Browser', () => {

    test('lifecycle states track properly', async () => {
        const storage = new EncryptedStorage();

        // 1. uninitialized before init
        expect(storage.getStatus()).toBe('uninitialized');
        expect(storage.isClosed()).toBe(false);
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

        // Store a payload to verify the database operations work fully with the new schema (no aad_context_json column)
        const schemaUuid = '00000000-0000-4000-8000-000000000001';
        const testPayload = { message: "hello browser" };
        const objectId = storage.storePayload(schemaUuid, 'application/json', testPayload);
        expect(objectId).toBeDefined();

        // Retrieve before lock
        const retrievedBeforeLock = storage.retrievePayload(objectId);
        expect(retrievedBeforeLock).toEqual(testPayload);

        // 6. Lock
        storage.lock();
        expect(storage.getStatus()).toBe('open_locked');
        expect(storage.isUnlocked()).toBe(false);

        // Retrieve fails when locked
        expect(() => storage.retrievePayload(objectId)).toThrow(errors.StorageLocked);

        // 7. Unlock
        await storage.unlockDatabase('pass');
        expect(storage.getStatus()).toBe('open_unlocked');

        // Retrieve succeeds after unlock, meaning key-wrap AAD was correctly built on the fly from wrapped_kid and wrapping_kid
        const retrievedAfterUnlock = storage.retrievePayload(objectId);
        expect(retrievedAfterUnlock).toEqual(testPayload);

        // Verify there is no aad_context_json column in wrapped_key_tbl
        const stmt = storage.db.prepare("PRAGMA table_info(wrapped_key_tbl)");
        let hasAadContextJson = false;
        while(stmt.step()) {
            if (stmt.get()[1] === 'aad_context_json') {
                hasAadContextJson = true;
            }
        }
        stmt.free();
        expect(hasAadContextJson).toBe(false);

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

    test('unlock failure clears keys', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('correct_pass', 'web');
        expect(storage.isUnlocked()).toBe(true);

        await expect(storage.unlockDatabase('wrong_pass')).rejects.toThrow(errors.UnlockFailed);

        expect(storage.isUnlocked()).toBe(false);
        expect(storage.getStatus()).toBe('open_locked');
    });

    test('duplicate initialize fails', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'web');

        await expect(storage.initializeDatabase('pass', 'web')).rejects.toThrow(errors.StorageAlreadyInitialized);

        storage.lock();
        await expect(storage.initializeDatabase('pass', 'web')).rejects.toThrow(errors.StorageAlreadyInitialized);
    });

    test('missing object raises ObjectNotFound', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('pass', 'web');
        expect(() => storage.retrievePayload('00000000-0000-0000-0000-000000000000')).toThrow(errors.ObjectNotFound);
        storage.close();
    });

    test('unsupported platform raises UnsupportedPlatform', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await expect(storage.initializeDatabase('pass', 'unknown_os')).rejects.toThrow(errors.UnsupportedPlatform);
        await expect(storage.initializeDatabase('pass', 'cross_platform')).rejects.toThrow(errors.UnsupportedPlatform);
        storage.close();
    });
});
