const fs = require('fs');
const path = require('path');
const os = require('os');
const { EncryptedStorage, errors } = require('../src');

const vectorsPath = path.join(__dirname, '../../test-vectors/uuid/uuid-v1.json');
const vectorsData = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));

describe('UUID Vectors Validation', () => {
    let dbPath;
    let storage;

    beforeEach(async () => {
        dbPath = path.join(os.tmpdir(), `test-${Date.now()}-${Math.random()}.sqlite`);
        storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase('pass', 'linux');
        await storage.unlockDatabase('pass');
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

    for (const vector of vectorsData.vectors) {
        test(`Vector: ${vector.description}`, async () => {
            const uuidVal = vector.uuid;
            const isValid = vector.valid;

            if (isValid) {
                // Should not throw
                await storage.storePayload(uuidVal, "application/json", {});
            } else {
                let caught = false;
                try {
                    await storage.storePayload(uuidVal, "application/json", {});
                } catch (e) {
                    caught = true;
                    expect(e).toBeInstanceOf(errors.InvalidUuid);
                }
                expect(caught).toBe(true);
            }
        });
    }
});
