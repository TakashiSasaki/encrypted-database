const path = require('path');
const { v4: uuidv4 } = require('uuid');
const EncryptedStorage = require('../../nodejs/src/storage');

async function main() {
    const dbPath = process.argv[2];
    const passphrase = process.argv[3];

    const storage = new EncryptedStorage(dbPath);
    await storage.initializeDatabase(passphrase, "linux");

    const schemaUuid = uuidv4();
    const contentType = "application/json";
    const payload = {"hello": "from nodejs"};

    const objUuid = storage.storePayload(schemaUuid, contentType, payload);
    console.log(objUuid);
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
