const fs = require('fs');
const path = require('path');
const { canonicalizeJson } = require('../src/crypto');

function loadJcsVectors() {
    const filePath = path.join(__dirname, '..', '..', 'test-vectors', 'jcs', 'rfc8785-basic.json');
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
}

describe('JCS Canonicalization Verification', () => {
    const vectors = loadJcsVectors();

    vectors.forEach(vector => {
        test(`vector: ${vector.name}`, () => {
            const actualBytes = canonicalizeJson(vector.input);

            // Verify byte-for-byte correctness (hex)
            expect(actualBytes.toString('hex')).toBe(vector.expected_hex);

            // Verify string equivalence
            expect(actualBytes.toString('utf8')).toBe(vector.expected_string);
        });
    });
});
