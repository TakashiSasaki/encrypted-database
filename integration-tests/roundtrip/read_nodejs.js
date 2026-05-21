const path = require('path');
const EncryptedStorage = require('../../nodejs/src/storage');
const assert = require('assert');

async function main() {
    if (process.argv.length < 5) {
        console.error("Usage: node read_nodejs.js <db_path> <passphrase> <obj_uuid>");
        process.exit(1);
    }

    const dbPath = process.argv[2];
    const passphrase = process.argv[3];
    const objUuid = process.argv[4];

    const storage = new EncryptedStorage(dbPath);
    try {
        await storage.unlockDatabase(passphrase);

        const payload = storage.retrievePayload(objUuid);

        const expectedPayload = {
            "secret": "cross-language",
            "value": 42,
            "nested": {
                "ok": true
            },
            "items": ["python", "nodejs"]
        };

        assert.deepStrictEqual(payload, expectedPayload, "Retrieved payload does not match expected payload.");

        console.log("PAYLOAD_MATCH_SUCCESS");
    } finally {
        storage.close();
    }
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
