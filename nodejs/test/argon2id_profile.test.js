const fs = require('fs');
const path = require('path');
const os = require('os');
const Database = require('better-sqlite3');
const EncryptedStorage = require('../src/storage');
const cryptoUtils = require('../src/crypto');

describe('Argon2id Profile V1', () => {
    let tempDbPath;

    beforeEach(() => {
        tempDbPath = path.join(os.tmpdir(), `test-db-${Math.random().toString(36).substring(7)}.sqlite`);
    });

    afterEach(() => {
        if (fs.existsSync(tempDbPath)) {
            fs.unlinkSync(tempDbPath);
        }
    });

    test('initialization saves correct profile in provider_config_json', async () => {
        const storage = new EncryptedStorage(tempDbPath);
        await storage.initializeDatabase('my_secure_password', 'linux');

        const db = new Database(tempDbPath);
        const row = db.prepare('SELECT provider_config_json FROM unlock_kek_tbl LIMIT 1').get();
        expect(row).toBeDefined();

        const config = JSON.parse(row.provider_config_json.toString('utf8'));

        expect(config.memory_kib).toBe(65536);
        expect(config.iterations).toBe(3);
        expect(config.parallelism).toBe(1);
        expect(config.salt).toBeDefined();

        const saltBuffer = Buffer.from(config.salt, 'base64url');
        expect(saltBuffer.length).toBe(16);

        const canonicalConfigStr = cryptoUtils.canonicalizeJson(config).toString('utf8');
        expect(row.provider_config_json.toString('utf8')).toBe(canonicalConfigStr);

        db.close();
        await storage.close();
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
    });
});
