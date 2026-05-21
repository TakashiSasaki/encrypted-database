const fs = require('fs');
const path = require('path');
const cryptoNode = require('crypto');
const { decryptAead } = require('../src/crypto');

function encryptAeadFixedNonce(key, nonce, plaintext, associatedData) {
    const cipher = cryptoNode.createCipheriv('aes-256-gcm', key, nonce);
    cipher.setAAD(associatedData);
    let ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final(), cipher.getAuthTag()]);
    return ciphertext; // returns ct+tag
}

describe('AEAD Vectors', () => {
    const vectorsPath = path.join(__dirname, '..', '..', 'test-vectors', 'aead', 'aes-256-gcm-v1.json');
    const vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));

    vectors.forEach((v) => {
        test(`AEAD vector '${v.name}'`, () => {
            const key = Buffer.from(v.key_hex, 'hex');
            const nonce = Buffer.from(v.nonce_hex, 'hex');
            const aad = Buffer.from(v.aad_hex, 'hex');
            const plaintext = Buffer.from(v.plaintext_hex, 'hex');
            const expectedCtTag = Buffer.from(v.expected_ciphertext_and_tag_hex, 'hex');

            // Encrypt
            const ctTag = encryptAeadFixedNonce(key, nonce, plaintext, aad);
            expect(ctTag).toEqual(expectedCtTag);

            // Decrypt
            const pt = decryptAead(key, nonce, ctTag, aad);
            expect(pt).toEqual(plaintext);

            // Negative: Corrupt tag
            const corruptedCtTag = Buffer.from(ctTag);
            corruptedCtTag[corruptedCtTag.length - 1] ^= 0xFF;
            expect(() => {
                decryptAead(key, nonce, corruptedCtTag, aad);
            }).toThrow();

            // Negative: Corrupt AAD
            const corruptedAad = Buffer.concat([aad, Buffer.from('a')]);
            expect(() => {
                decryptAead(key, nonce, ctTag, corruptedAad);
            }).toThrow();
        });
    });
});
