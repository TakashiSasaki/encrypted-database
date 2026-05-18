const crypto = require('crypto');
const argon2 = require('argon2-browser');

function generateRandomBytes(length = 32) {
    return crypto.randomBytes(length);
}

function generateNonce() {
    return crypto.randomBytes(12);
}

async function deriveKekArgon2id(password, salt, length = 32, timeCost = 3, memoryCost = 262144, parallelism = 4) {
    // Note: Since browsers have strict memory limits for WebAssembly,
    // memoryCost might need to be adjusted for very low-end devices,
    // but we use the provided arguments for the test as requested.
    const result = await argon2.hash({
        pass: password,
        salt: salt,
        type: argon2.ArgonType.Argon2id,
        hashLen: length,
        time: timeCost,
        mem: memoryCost,
        parallelism: parallelism,
    });
    return Buffer.from(result.hash);
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
