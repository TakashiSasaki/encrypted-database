const crypto = require('crypto');
const argon2 = require('argon2');

function generateRandomBytes(length = 32) {
    return crypto.randomBytes(length);
}

function generateNonce() {
    return crypto.randomBytes(12);
}

async function deriveKekArgon2id(password, salt, length = 32, timeCost = 3, memoryCost = 262144, parallelism = 4) {
    return argon2.hash(password, {
        type: argon2.argon2id,
        salt: salt,
        hashLength: length,
        timeCost: timeCost,
        memoryCost: memoryCost,
        parallelism: parallelism,
        raw: true
    });
}

function encryptAead(key, plaintext, associatedData) {
    const nonce = generateNonce();
    const cipher = crypto.createCipheriv('aes-256-gcm', key, nonce);
    cipher.setAAD(associatedData);
    let ciphertext = Buffer.concat([cipher.update(plaintext), cipher.final(), cipher.getAuthTag()]);
    return { nonce, ciphertext };
}

function decryptAead(key, nonce, ciphertextWithTag, associatedData) {
    const tag = ciphertextWithTag.slice(-16);
    const ciphertext = ciphertextWithTag.slice(0, -16);
    const decipher = crypto.createDecipheriv('aes-256-gcm', key, nonce);
    decipher.setAAD(associatedData);
    decipher.setAuthTag(tag);
    return Buffer.concat([decipher.update(ciphertext), decipher.final()]);
}

const { canonicalize } = require('json-canonicalize');

function canonicalizeJson(data) {
    // Uses json-canonicalize for RFC 8785 JSON Canonicalization Scheme
    return Buffer.from(canonicalize(data), 'utf8');
}

module.exports = {
    generateRandomBytes,
    generateNonce,
    deriveKekArgon2id,
    encryptAead,
    decryptAead,
    canonicalizeJson
};
