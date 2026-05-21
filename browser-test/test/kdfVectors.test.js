const fs = require('fs');
const path = require('path');
const { deriveKekArgon2id } = require('../src/crypto');
const cryptoNode = require('crypto');

// Polyfills
global.crypto = {
    getRandomValues: (buffer) => cryptoNode.randomFillSync(buffer)
};
global.TextEncoder = require('util').TextEncoder;
global.TextDecoder = require('util').TextDecoder;

describe('KDF Vectors (Browser)', () => {
    beforeAll(async () => {

    });

    const vectorsPath = path.join(__dirname, '..', '..', 'test-vectors', 'kdf', 'argon2id-v1.json');
    const vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));

    vectors.forEach((v) => {
        if (v.kdf !== 'argon2id') return;

        test(`KDF vector '${v.name}'`, async () => {
            const salt = new Uint8Array(Buffer.from(v.salt_hex, 'hex'));
            const expected = new Uint8Array(Buffer.from(v.expected_kek_hex, 'hex'));

            const derived = await deriveKekArgon2id(
                v.passphrase,
                salt,
                v.length,
                v.time_cost,
                v.memory_kib,
                v.parallelism
            );

            expect(Buffer.from(derived)).toEqual(Buffer.from(expected));
        });
    });
});
