const fs = require('fs');
const path = require('path');
const { deriveKekArgon2id } = require('../src/crypto');

describe('KDF Vectors', () => {
    const vectorsPath = path.join(__dirname, '..', '..', 'test-vectors', 'kdf', 'argon2id-v1.json');
    const vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));

    vectors.forEach((v) => {
        if (v.kdf !== 'argon2id') return;

        test(`KDF vector '${v.name}'`, async () => {
            const salt = Buffer.from(v.salt_hex, 'hex');
            const expected = Buffer.from(v.expected_kek_hex, 'hex');

            const derived = await deriveKekArgon2id(
                v.passphrase,
                salt,
                v.length,
                v.time_cost,
                v.memory_kib,
                v.parallelism
            );

            expect(derived).toEqual(expected);
        });
    });
});
