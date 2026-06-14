const fs = require('fs');
const path = require('path');
const { canonicalizeJson } = require('../src/crypto');

function loadJcsVectors() {
    let allVectors = [];
    const files = ['rfc8785-basic.json', 'generic-positive-coverage.json'];
    for (const fileName of files) {
        const filePath = path.join(__dirname, '..', '..', 'test-vectors', 'jcs', fileName);
        const data = fs.readFileSync(filePath, 'utf8');
        const fileVectors = JSON.parse(data);
        fileVectors.forEach(v => v._file = fileName);
        allVectors = allVectors.concat(fileVectors);
    }
    return allVectors;
}

describe('JCS Canonicalization Verification', () => {
    const vectors = loadJcsVectors();

    vectors.forEach(vector => {
        test(`vector: ${vector._file}:${vector.name}`, () => {
            const actualBytes = canonicalizeJson(vector.input);

            // Verify byte-for-byte correctness (hex)
            expect(actualBytes.toString('hex')).toBe(vector.expected_hex);

            // Verify string equivalence
            expect(actualBytes.toString('utf8')).toBe(vector.expected_string);
        });
    });
});
