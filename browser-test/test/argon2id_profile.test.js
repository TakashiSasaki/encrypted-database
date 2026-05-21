const fs = require('fs');
const path = require('path');
const EncryptedStorage = require('../src/storage');
const cryptoUtils = require('../src/crypto');

describe('Argon2id Profile V1', () => {

    test('initialization saves correct profile in provider_config_json', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase('my_secure_password', 'linux');

        const stmt = storage.db.prepare('SELECT provider_config_json FROM unlock_kek_tbl LIMIT 1');
        expect(stmt.step()).toBe(true);
        const row = stmt.getAsObject();
        expect(row.provider_config_json).toBeDefined();

        const config = JSON.parse(Buffer.from(row.provider_config_json).toString('utf8'));

        expect(config.memory_kib).toBe(65536);
        expect(config.iterations).toBe(3);
        expect(config.parallelism).toBe(1);
        expect(config.salt).toBeDefined();

        const saltBuffer = Buffer.from(config.salt, 'base64url');
        expect(saltBuffer.length).toBe(16);

        const providerConfigStr = Buffer.from(row.provider_config_json).toString('utf8');
        const canonicalConfigStr = cryptoUtils.canonicalizeJson(config).toString('utf8');
        expect(providerConfigStr).toBe(canonicalConfigStr);

        stmt.free();
        storage.close();
    });

    test('argon2id test vector', async () => {
        const vectorPath = path.join(__dirname, '..', '..', 'test-vectors', 'kdf', 'argon2id-v1.json');
        const vectors = JSON.parse(fs.readFileSync(vectorPath, 'utf8'));
        const vector = vectors[0];

        const passphrase = vector.input.passphrase;
        const salt = Buffer.from(vector.input.salt_hex, 'hex');

        const expectedOutputHex = vector.expected_output_hex;

        const derived = await cryptoUtils.deriveKekArgon2id(
            passphrase,
            salt,
            vector.parameters.output_bytes,
            vector.parameters.iterations,
            vector.parameters.memory_kib,
            vector.parameters.parallelism
        );

        expect(derived.toString('hex')).toBe(expectedOutputHex);
    }, 20000); // Give extra time for WASM Argon2id execution
});
