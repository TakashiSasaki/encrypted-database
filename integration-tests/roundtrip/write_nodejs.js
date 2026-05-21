const path = require('path');
const EncryptedStorage = require('../../nodejs/src/storage');

async function main() {
    if (process.argv.length < 4) {
        console.error("Usage: node write_nodejs.js <db_path> <passphrase>");
        process.exit(1);
    }

    const dbPath = process.argv[2];
    const passphrase = process.argv[3];

    const storage = new EncryptedStorage(dbPath);
    try {
        await storage.initializeDatabase(passphrase, "linux");

        const schemaUuid = "00000000-0000-4000-8000-000000000001";
        const contentType = "application/json";
        const payload = {
            "secret": "cross-language",
            "value": 42,
            "nested": {
                "ok": true
            },
            "items": ["python", "nodejs"]
        };

        const objUuid = storage.storePayload(schemaUuid, contentType, payload);
        console.log(objUuid);
    } finally {
        storage.close();
    }
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
