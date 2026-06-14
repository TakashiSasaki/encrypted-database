const packageRoot = require('..');

describe('Node.js Package Entrypoint', () => {
    test('exports EncryptedStorage', () => {
        expect(packageRoot.EncryptedStorage).toBeDefined();
        expect(typeof packageRoot.EncryptedStorage).toBe('function');
    });

    test('exports error classes', () => {
        expect(packageRoot.errors).toBeDefined();
        expect(packageRoot.errors.StorageError).toBeDefined();
        expect(packageRoot.errors.ObjectNotFound).toBeDefined();

        // Also check destructured errors
        expect(packageRoot.StorageError).toBeDefined();
        expect(packageRoot.ObjectNotFound).toBeDefined();
    });
});
