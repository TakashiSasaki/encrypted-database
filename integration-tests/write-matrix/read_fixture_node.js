const path = require('path');

// Try requiring the local Node.js module
let EncryptedStorage;
let cryptoUtils;
try {
    const storageMod = require('../../nodejs/src/storage');
    // CommonJS export handles differ between module patterns, but here it's typically direct export if it's not index.js
    EncryptedStorage = storageMod;
    if (typeof storageMod.EncryptedStorage !== 'undefined') {
        EncryptedStorage = storageMod.EncryptedStorage;
    }
    cryptoUtils = require('../../nodejs/src/crypto');
} catch (e) {
    console.error(`Error: Node.js dependencies not met. Run 'npm ci' in nodejs/. Details: ${e.message}`);
    process.exit(1);
}

async function main() {
    if (process.argv.length !== 5) {
        console.error("Usage: node read_fixture_node.js <db_path> <passphrase> <object_uuid>");
        process.exit(1);
    }

    const dbPath = process.argv[2];
    const passphrase = process.argv[3];
    const objectUuid = process.argv[4];

    let storage;
    try {
        storage = new EncryptedStorage(dbPath);
        await storage.unlockDatabase(passphrase);
        const payload = storage.retrievePayload(objectUuid);

        // Canonicalize using JCS and output hex
        const canonicalBytes = cryptoUtils.canonicalizeJson(payload);
        const payloadHex = canonicalBytes.toString('hex').toLowerCase();

        const output = {
            object_uuid: objectUuid,
            payload_hex: payloadHex
        };
        console.log(JSON.stringify(output));
    } catch (e) {
        console.error(`Error during Node.js read: ${e.message}`);
        process.exit(1);
    } finally {
        if (storage) {
            storage.close();
        }
    }
}

main();
