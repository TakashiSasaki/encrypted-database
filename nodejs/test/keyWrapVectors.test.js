const fs = require('fs');
const path = require('path');
const cryptoNode = require('crypto');
const { decryptAead } = require('../src/crypto');
const { buildAadBytes } = require('../src/aadPolicy');

function encryptAeadFixedNonce(key, nonce, plaintext, associatedData) {
    const cipher = cryptoNode.createCipheriv('aes-256-gcm', key, nonce);
    cipher.setAAD(associatedData);
    let ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final(), cipher.getAuthTag()]);
    return ciphertext;
}

describe('Key Wrap Vectors', () => {
    const vectorsPath = path.join(__dirname, '..', '..', 'test-vectors', 'key-wrap', 'key-wrap-v1.json');
    const vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));

    vectors.forEach((v) => {
        test(`Key-wrap vector '${v.name}'`, () => {
            const wrappingKey = Buffer.from(v.wrapping_key_hex, 'hex');
            const nonce = Buffer.from(v.nonce_hex, 'hex');
            const wrappedKeyPt = Buffer.from(v.wrapped_key_plaintext_hex, 'hex');
            const expectedCtTag = Buffer.from(v.expected_wrapped_key_ciphertext_and_tag_hex, 'hex');
            const expectedAad = Buffer.from(v.expected_aad_hex, 'hex');

            // Generate AAD dynamically
            const aadBytes = buildAadBytes(v.aad_policy, {
                wrapped_kid: v.wrapped_kid,
                wrapping_kid: v.wrapping_kid
            });
            expect(aadBytes).toEqual(expectedAad);

            // Wrap (Encrypt)
            const ctTag = encryptAeadFixedNonce(wrappingKey, nonce, wrappedKeyPt, aadBytes);
            expect(ctTag).toEqual(expectedCtTag);

            // Unwrap (Decrypt)
            const pt = decryptAead(wrappingKey, nonce, ctTag, aadBytes);
            expect(pt).toEqual(wrappedKeyPt);
        });
    });
});
