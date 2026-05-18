const fs = require('fs');
const path = require('path');
const { canonicalizeJson } = require('../src/crypto');

const INPUT_DIR = path.join(__dirname, 'testdata', 'input');
const OUTPUT_DIR = path.join(__dirname, 'testdata', 'output');

describe('RFC 8785 Canonicalization', () => {
    let testVectors = [];

    if (fs.existsSync(INPUT_DIR)) {
        testVectors = fs.readdirSync(INPUT_DIR).filter(file => file.endsWith('.json'));
    }

    if (testVectors.length === 0) {
        test('RFC 8785 test vectors are available', () => {
            throw new Error(
                fs.existsSync(INPUT_DIR)
                    ? `No RFC 8785 test vectors found in ${INPUT_DIR}`
                    : `Required RFC 8785 test vector directory is missing: ${INPUT_DIR}`
            );
        });
    }

    testVectors.forEach(filename => {
        test(`Canonicalizes ${filename} correctly`, () => {
            const inputPath = path.join(INPUT_DIR, filename);
            const outputPath = path.join(OUTPUT_DIR, filename);

            const inputDataStr = fs.readFileSync(inputPath, 'utf8');
            const expectedOutput = fs.readFileSync(outputPath);

            const inputData = JSON.parse(inputDataStr);
            const canonicalized = canonicalizeJson(inputData);

            expect(canonicalized).toEqual(expectedOutput);
        });
    });
});
