const fs = require('fs');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');
const path = require('path');
const os = require('os');

describe('Input Validation', () => {
    let dbPath;
    let storage;

    beforeEach(() => {
        dbPath = path.join(os.tmpdir(), `test-${Date.now()}-${Math.random()}.sqlite`);
        storage = new EncryptedStorage(dbPath);
    });

    afterEach(() => {
        try {
            if (storage && !storage.isClosed()) {
                storage.close();
            }
        } catch (e) {}
        if (fs.existsSync(dbPath)) {
            fs.unlinkSync(dbPath);
        }
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

        // Top level rejections
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', []);
        }).toThrow(errors.InvalidPayload);

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', 'string');
        }).toThrow(errors.InvalidPayload);

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', null);
        }).toThrow(errors.InvalidPayload);

        // Valid deeply nested payload
        const validPayload = {
            a: "string",
            b: 123,
            c: 45.67,
            d: true,
            e: false,
            f: null,
            g: [1, "two", { three: 3 }],
            h: { nested: { deep: [true, false, null] } },
            i: Object.create(null) // prototype null is allowed
        };
        validPayload.i.j = 4;

        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', validPayload);
        }).not.toThrow();

        // Binary and buffers
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: Buffer.from('data') });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: new ArrayBuffer(8) });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: new Uint8Array(8) });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: new DataView(new ArrayBuffer(8)) });
        }).toThrow(errors.InvalidPayload);

        // Objects
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: new Date() });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: new Map() });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: new Set() });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: /regex/ });
        }).toThrow(errors.InvalidPayload);

        class Dummy {}
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: new Dummy() });
        }).toThrow(errors.InvalidPayload);

        // Cyclic references
        const cyclicObj = {};
        cyclicObj.self = cyclicObj;
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', cyclicObj);
        }).toThrow(errors.InvalidPayload);

        const cyclicArray = [];
        cyclicArray.push(cyclicArray);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { data: cyclicArray });
        }).toThrow(errors.InvalidPayload);

        // Primitives
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { num: NaN });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { num: Infinity });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { num: -Infinity });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { val: undefined });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { val: Symbol('sym') });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { val: 123n });
        }).toThrow(errors.InvalidPayload);
        expect(() => {
            storage.storePayload(schemaUuid, 'application/json', { val: () => {} });
        }).toThrow(errors.InvalidPayload);
    });

    test('validates passphrase correctly', async () => {
        await expect(storage.initializeDatabase(null, 'linux')).rejects.toThrow(TypeError);

        // Empty string should be allowed
        await storage.initializeDatabase('', 'linux');
        expect(storage.isUnlocked()).toBe(true);

        storage.close();

        storage = new EncryptedStorage(dbPath);
        await expect(storage.unlockDatabase(null)).rejects.toThrow(TypeError);
    });

    test('closed state precedence', async () => {
        await storage.initializeDatabase('pass', 'linux');
        storage.close();

        expect(() => {
            storage.storePayload('invalid-uuid', '', []);
        }).toThrow(errors.StorageClosed);

        expect(() => {
            storage.retrievePayload('invalid-uuid');
        }).toThrow(errors.StorageClosed);

        await expect(storage.initializeDatabase(123, 456)).rejects.toThrow(errors.StorageClosed);
        await expect(storage.unlockDatabase(123)).rejects.toThrow(errors.StorageClosed);
    });
});
