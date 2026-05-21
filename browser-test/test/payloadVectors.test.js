const fs = require('fs');
const path = require('path');
const cryptoNode = require('crypto');
const { decryptAead, canonicalizeJson } = require('../src/crypto');
const { buildAadBytes } = require('../src/aadPolicy');

function encryptAeadFixedNonce(key, nonce, plaintext, associatedData) {
    const cipher = cryptoNode.createCipheriv('aes-256-gcm', key, nonce);
    cipher.setAAD(associatedData);
    let ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final(), cipher.getAuthTag()]);
    return ciphertext;
}

global.TextEncoder = require('util').TextEncoder;
global.TextDecoder = require('util').TextDecoder;

describe('Payload Vectors (Browser)', () => {
    const vectorsPath = path.join(__dirname, '..', '..', 'test-vectors', 'payload', 'payload-encryption-v1.json');
    const vectors = JSON.parse(fs.readFileSync(vectorsPath, 'utf8'));

    vectors.forEach((v) => {
        test(`Payload vector '${v.name}'`, async () => {
            const recordDek = Buffer.from(v.record_dek_hex, 'hex');
            const nonce = Buffer.from(v.nonce_hex, 'hex');
            const expectedAad = Buffer.from(v.expected_aad_hex, 'hex');
            const expectedCtTag = Buffer.from(v.expected_ciphertext_and_tag_hex, 'hex');
            const expectedJcs = Buffer.from(v.expected_payload_jcs, 'utf8');

            // AAD
            const aadBytes = buildAadBytes('record-payload-v1', {
                object_uuid: v.object_uuid,
                schema_uuid: v.schema_uuid,
                content_type: v.content_type,
                kid: v.kid,
                alg: v.alg
            });
            expect(aadBytes).toEqual(expectedAad);

            // JCS
            const payloadJcs = canonicalizeJson(v.payload_json);
            expect(payloadJcs).toEqual(expectedJcs);

            // Encrypt
            const ctTag = encryptAeadFixedNonce(recordDek, nonce, payloadJcs, aadBytes);
            expect(ctTag).toEqual(expectedCtTag);

            // Decrypt
            const pt = decryptAead(recordDek, nonce, ctTag, aadBytes);
            expect(pt).toEqual(expectedJcs);

            // Reorder keys
            const reorderedPayload = {};
            const keys = Object.keys(v.payload_json).reverse();
            keys.forEach(k => {
                reorderedPayload[k] = v.payload_json[k];
            });
            const reorderedJcs = canonicalizeJson(reorderedPayload);
            expect(reorderedJcs).toEqual(expectedJcs);
        });
    });
});
