const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const aadPolicy = require('../src/aadPolicy');

const VECTOR_PATH = path.join(__dirname, '../../test-vectors/key-wrap/key-wrap-v1.json');
const vectors = JSON.parse(fs.readFileSync(VECTOR_PATH, 'utf8'));

describe('Key Wrap Vectors', () => {
    vectors.forEach(vector => {
        test(vector.name, () => {
            const wrappingKey = Buffer.from(vector.wrapping_key_hex, 'hex');
            const wrappedKeyPlaintext = Buffer.from(vector.wrapped_key_plaintext_hex, 'hex');
            const nonce = Buffer.from(vector.nonce_hex, 'hex');
            const expectedAad = Buffer.from(vector.expected_aad_hex, 'hex');
            const expectedCiphertextAndTag = Buffer.from(vector.expected_wrapped_key_ciphertext_and_tag_hex, 'hex');

            // Verify AAD construction
            const actualAad = aadPolicy.buildAadBytes(vector.aad_policy, {
                wrapped_kid: vector.wrapped_kid,
                wrapping_kid: vector.wrapping_kid
            });
            expect(actualAad.toString('hex')).toBe(expectedAad.toString('hex'));

            if (vector.valid) {
                // Encrypt
                const cipher = crypto.createCipheriv('aes-256-gcm', wrappingKey, nonce);
                cipher.setAAD(actualAad);
                const ciphertext = Buffer.concat([cipher.update(wrappedKeyPlaintext), cipher.final()]);
                const tag = cipher.getAuthTag();
                const ciphertextAndTag = Buffer.concat([ciphertext, tag]);

                expect(ciphertextAndTag.toString('hex')).toBe(expectedCiphertextAndTag.toString('hex'));

                // Decrypt
                const decipher = crypto.createDecipheriv('aes-256-gcm', wrappingKey, nonce);
                decipher.setAAD(actualAad);
                decipher.setAuthTag(expectedCiphertextAndTag.slice(-16));
                const decrypted = Buffer.concat([decipher.update(expectedCiphertextAndTag.slice(0, -16)), decipher.final()]);

                expect(decrypted.toString('hex')).toBe(wrappedKeyPlaintext.toString('hex'));
            } else {
                const decipher = crypto.createDecipheriv('aes-256-gcm', wrappingKey, nonce);
                decipher.setAAD(actualAad);
                decipher.setAuthTag(expectedCiphertextAndTag.slice(-16));
                expect(() => {
                    Buffer.concat([decipher.update(expectedCiphertextAndTag.slice(0, -16)), decipher.final()]);
                }).toThrow();
            }
        });
    });
});
