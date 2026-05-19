const fs = require('fs');
const path = require('path');
const { canonicalizeJson } = require('../src/crypto');

const INPUT_DIR = path.join(__dirname, 'testdata', 'input');
const OUTPUT_DIR = path.join(__dirname, 'testdata', 'output');

describe('RFC 8785 Canonicalization', () => {
    let testVectors = [];

    if (fs.existsSync(INPUT_DIR)) {
        testVectors = fs.readdirSync(INPUT_DIR).filter(file => file.endsWith('.json'));
    }

    if (testVectors.length === 0) {
        test('RFC 8785 test vectors are available', () => {
            throw new Error(
                fs.existsSync(INPUT_DIR)
                    ? `No RFC 8785 test vectors found in ${INPUT_DIR}`
                    : `Required RFC 8785 test vector directory is missing: ${INPUT_DIR}`
            );
        });
    }

    testVectors.forEach(filename => {
        test(`Canonicalizes ${filename} correctly`, () => {
            const inputPath = path.join(INPUT_DIR, filename);
            const outputPath = path.join(OUTPUT_DIR, filename);

            const inputDataStr = fs.readFileSync(inputPath, 'utf8');
            const expectedOutput = fs.readFileSync(outputPath);

            const inputData = JSON.parse(inputDataStr);
            const canonicalized = canonicalizeJson(inputData);

            expect(canonicalized).toEqual(expectedOutput);
        });
    });
});

const { generateRandomBytes, generateNonce, deriveKekArgon2id, encryptAead, decryptAead } = require('../src/crypto');

describe('Crypto functions', () => {
    test('generateRandomBytes', () => {
        const bytes = generateRandomBytes(32);
        expect(bytes.length).toBe(32);
        // Test default length
        expect(generateRandomBytes().length).toBe(32);
    });

    test('generateNonce', () => {
        const nonce = generateNonce();
        expect(nonce.length).toBe(12);
    });

    test('deriveKekArgon2id', async () => {
        const password = 'my_secure_password';
        const salt = generateRandomBytes(16);
        const derivedKey = await deriveKekArgon2id(password, salt, 32, 2, 1024, 1);
        expect(derivedKey.length).toBe(32);

        // test defaults
        const d2 = await deriveKekArgon2id(password, salt);
        expect(d2.length).toBe(32);
    });

    test('encrypt and decrypt', () => {
        const key = generateRandomBytes(32);
        const plaintext = Buffer.from('hello world');
        const associatedData = Buffer.from('metadata');

        const { nonce, ciphertext } = encryptAead(key, plaintext, associatedData);

        const decrypted = decryptAead(key, nonce, ciphertext, associatedData);
        expect(decrypted).toEqual(plaintext);
    });
});
