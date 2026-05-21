const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const VECTOR_PATH = path.join(__dirname, '../../test-vectors/aead/aes-256-gcm-v1.json');
const vectors = JSON.parse(fs.readFileSync(VECTOR_PATH, 'utf8'));

describe('AEAD Test Vectors', () => {
    vectors.forEach(vector => {
        test(vector.name, () => {
            const key = Buffer.from(vector.key_hex, 'hex');
            const nonce = Buffer.from(vector.nonce_hex, 'hex');
            const aad = Buffer.from(vector.aad_hex, 'hex');
            const plaintext = Buffer.from(vector.plaintext_hex, 'hex');

            const expectedCiphertextAndTag = Buffer.from(vector.expected_ciphertext_and_tag_hex, 'hex');
            const expectedCiphertext = Buffer.from(vector.expected_ciphertext_hex, 'hex');
            const expectedTag = Buffer.from(vector.expected_tag_hex, 'hex');

            if (vector.valid) {
                // Encrypt
                const cipher = crypto.createCipheriv('aes-256-gcm', key, nonce);
                cipher.setAAD(aad);
                const ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final()]);
                const tag = cipher.getAuthTag();
                const ciphertextAndTag = Buffer.concat([ciphertext, tag]);

                expect(ciphertext.toString('hex')).toBe(expectedCiphertext.toString('hex'));
                expect(tag.toString('hex')).toBe(expectedTag.toString('hex'));
                expect(ciphertextAndTag.toString('hex')).toBe(expectedCiphertextAndTag.toString('hex'));

                // Decrypt
                const decipher = crypto.createDecipheriv('aes-256-gcm', key, nonce);
                decipher.setAAD(aad);
                decipher.setAuthTag(expectedTag);
                const decrypted = Buffer.concat([decipher.update(expectedCiphertext), decipher.final()]);
                expect(decrypted.toString('hex')).toBe(plaintext.toString('hex'));
            } else {
                // Decrypt should fail
                const decipher = crypto.createDecipheriv('aes-256-gcm', key, nonce);
                decipher.setAAD(aad);
                // expectedCiphertextAndTag might be modified in negative tests, extract tag properly
                const modTag = expectedCiphertextAndTag.slice(-16);
                const modCiphertext = expectedCiphertextAndTag.slice(0, -16);
                decipher.setAuthTag(modTag);

                expect(() => {
                    Buffer.concat([decipher.update(modCiphertext), decipher.final()]);
                }).toThrow();
            }
        });
    });
});
