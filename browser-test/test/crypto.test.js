const { generateRandomBytes, generateNonce, encryptAead, decryptAead, canonicalizeJson } = require('../src/crypto');

describe('Crypto Utility Tests', () => {
  it('should generate random bytes of correct length', () => {
    const bytes = generateRandomBytes(32);
    expect(bytes).toHaveLength(32);
  });

  it('should generate a 12-byte nonce', () => {
    const nonce = generateNonce();
    expect(nonce).toHaveLength(12);
  });

  it('should accurately encrypt and decrypt AEAD data', () => {
    const key = generateRandomBytes(32);
    const plaintext = Buffer.from('hello world');
    const aad = Buffer.from('metadata');

    const { nonce, ciphertext } = encryptAead(key, plaintext, aad);
    const decrypted = decryptAead(key, nonce, ciphertext, aad);

    expect(decrypted.toString()).toBe('hello world');
  });

  it('should fail decryption if AAD is tampered', () => {
    const key = generateRandomBytes(32);
    const plaintext = Buffer.from('hello world');
    const aad = Buffer.from('metadata');

    const { nonce, ciphertext } = encryptAead(key, plaintext, aad);
    const wrongAad = Buffer.from('wrong_metadata');

    expect(() => decryptAead(key, nonce, ciphertext, wrongAad)).toThrow();
  });

  it('should canonicalize JSON as RFC 8785', () => {
    const obj1 = { b: 1, a: 2 };
    const obj2 = { a: 2, b: 1 };

    const can1 = canonicalizeJson(obj1);
    const can2 = canonicalizeJson(obj2);

    expect(can1.toString('utf8')).toBe('{"a":2,"b":1}');
    expect(can1).toEqual(can2);
  });
});
