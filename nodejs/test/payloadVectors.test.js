const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const cryptoUtils = require('../src/crypto');

const VECTOR_PATH = path.join(__dirname, '../../test-vectors/payload/payload-encryption-v1.json');
const vectors = JSON.parse(fs.readFileSync(VECTOR_PATH, 'utf8'));

describe('Payload Vectors', () => {
    vectors.forEach(vector => {
        test(vector.name, () => {
            const recordDek = Buffer.from(vector.record_dek_hex, 'hex');
            const nonce = Buffer.from(vector.nonce_hex, 'hex');
            const expectedAad = Buffer.from(vector.expected_aad_hex, 'hex');
            const expectedPayloadJcs = Buffer.from(vector.expected_payload_jcs_hex, 'hex');
            const expectedCiphertextAndTag = Buffer.from(vector.expected_ciphertext_and_tag_hex, 'hex');

            // Verify JCS
            const actualPayloadJcs = cryptoUtils.canonicalizeJson(vector.payload_json);
            expect(actualPayloadJcs.toString('hex')).toBe(expectedPayloadJcs.toString('hex'));

            if (vector.valid) {
                // Encrypt
                const cipher = crypto.createCipheriv('aes-256-gcm', recordDek, nonce);
                cipher.setAAD(expectedAad);
                const ciphertext = Buffer.concat([cipher.update(actualPayloadJcs), cipher.final()]);
                const tag = cipher.getAuthTag();
                const ciphertextAndTag = Buffer.concat([ciphertext, tag]);

                expect(ciphertextAndTag.toString('hex')).toBe(expectedCiphertextAndTag.toString('hex'));

                // Decrypt
                const decipher = crypto.createDecipheriv('aes-256-gcm', recordDek, nonce);
                decipher.setAAD(expectedAad);
                decipher.setAuthTag(expectedCiphertextAndTag.slice(-16));
                const decrypted = Buffer.concat([decipher.update(expectedCiphertextAndTag.slice(0, -16)), decipher.final()]);

                expect(decrypted.toString('hex')).toBe(actualPayloadJcs.toString('hex'));
            } else {
                const decipher = crypto.createDecipheriv('aes-256-gcm', recordDek, nonce);
                decipher.setAAD(expectedAad);
                decipher.setAuthTag(expectedCiphertextAndTag.slice(-16));
                expect(() => {
                    Buffer.concat([decipher.update(expectedCiphertextAndTag.slice(0, -16)), decipher.final()]);
                }).toThrow();
            }
        });
    });
});
