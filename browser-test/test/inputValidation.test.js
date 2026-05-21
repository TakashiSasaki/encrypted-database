const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');

describe('Input Validation', () => {
    let storage;

    beforeEach(async () => {
        storage = new EncryptedStorage();
        await storage.init();
    });

    afterEach(() => {
        try {
            if (storage && !storage.isClosed()) {
                storage.close();
            }
        } catch (e) {}
    });

    test('validates UUID correctly', async () => {
        await storage.initializeDatabase('pass', 'linux');

        const validUuid = '12345678-1234-4234-8234-123456789012';

        expect(() => {
            storage.storePayload(validUuid.replace(/-/g, ''), 'application/json', {});
        }).toThrow(errors.InvalidUuid);

        expect(() => {
            storage.storePayload('A2345678-1234-4234-8234-123456789012', 'application/json', {});
        }).toThrow(errors.InvalidUuid);

        expect(() => {
            storage.storePayload(null, 'application/json', {});
        }).toThrow(errors.InvalidUuid);

        expect(() => {
            storage.retrievePayload('invalid-uuid');
        }).toThrow(errors.InvalidUuid);
    });

    test('validates content type correctly', async () => {
        await storage.initializeDatabase('pass', 'linux');
        const schemaUuid = '12345678-1234-4234-8234-123456789012';

        expect(() => {
            storage.storePayload(schemaUuid, '', {});
        }).toThrow(errors.InvalidContentType);

        expect(() => {
            storage.storePayload(schemaUuid, 'applicationjson', {});
        }).toThrow(errors.InvalidContentType);

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json\x00', {});
        }).toThrow(errors.InvalidContentType);
    });

    test('validates payload correctly', async () => {
        await storage.initializeDatabase('pass', 'linux');
        const schemaUuid = '12345678-1234-4234-8234-123456789012';

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', []);
        }).toThrow(errors.InvalidPayload);

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', 'string');
        }).toThrow(errors.InvalidPayload);

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', null);
        }).toThrow(errors.InvalidPayload);

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', new Uint8Array([1, 2, 3]));
        }).toThrow(errors.InvalidPayload);
    });

    test('validates passphrase correctly', async () => {
        await expect(storage.initializeDatabase(null, 'linux')).rejects.toThrow(errors.UnlockFailed);

        // Empty string should be allowed
        await storage.initializeDatabase('', 'linux');
        expect(storage.isUnlocked()).toBe(true);
    });
});
