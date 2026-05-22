const EncryptedStorage = require('../src/storage');

describe('Provider Config Canonicalization Browser', () => {
    test('provider_config_json is canonicalized in database', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('test_passphrase', 'web');

        const db = storage.db;
        const res = db.exec("SELECT provider_config_json FROM unlock_kek_tbl LIMIT 1");
        expect(res).toBeDefined();
        expect(res.length).toBeGreaterThan(0);

        const jsonStr = res[0].values[0][0];

        // Assert that the JSON string doesn't contain spaces after colons/commas, which is characteristic of JSON.stringify vs canonicalizeJson
        expect(jsonStr).not.toMatch(/:\s/);
        expect(jsonStr).not.toMatch(/,\s/);

        // Keys should be ordered lexicographically
        // "iterations", "kdf", "memory_kib", "output_bytes", "parallelism", "profile", "salt"
        const parsed = JSON.parse(jsonStr);
        expect(Object.keys(parsed)).toEqual(["iterations", "kdf", "memory_kib", "output_bytes", "parallelism", "profile", "salt"]);

        // A canonicalized JSON string must exactly match this format:
        const expectedPrefix = '{"iterations":';
        expect(jsonStr.startsWith(expectedPrefix)).toBe(true);
    });
});
