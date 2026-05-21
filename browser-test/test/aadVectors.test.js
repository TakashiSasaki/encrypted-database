const fs = require('fs');
const path = require('path');
const { buildAadBytes, buildAadContext } = require('../src/aadPolicy');

function loadAadVectors() {
    const filePath = path.join(__dirname, '..', '..', 'test-vectors', 'aad', 'aad-policies-v1.json');
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
}

function loadNegativeAadVectors() {
    const filePath = path.join(__dirname, '..', '..', 'test-vectors', 'aad', 'aad-negative.json');
    const data = fs.readFileSync(filePath, 'utf8');
    return JSON.parse(data);
}

describe('AAD Vectors Verification', () => {
    const vectors = loadAadVectors();
    const negativeVectors = loadNegativeAadVectors();

    vectors.forEach(vector => {
        test(`vector: ${vector.name}`, () => {
            // Verify context building
            const actualContext = buildAadContext(vector.policy, vector.input);
            expect(actualContext).toEqual(vector.expected_context);

            // Verify canonicalized AAD bytes
            const actualBytes = buildAadBytes(vector.policy, vector.input);
            expect(actualBytes.toString('hex')).toBe(vector.expected_hex);
            expect(actualBytes.toString('utf8')).toBe(vector.expected_string);
        });
    });

    negativeVectors.forEach(vector => {
        test(`negative vector: ${vector.description}`, () => {
            expect(() => {
                buildAadBytes(vector.policy, vector.args);
            }).toThrow(new RegExp(vector.expected_error));
        });
    });
});
