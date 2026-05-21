const path = require('path');
const EncryptedStorage = require('../../nodejs/src/storage');

async function main() {
    const dbPath = process.argv[2];
    const passphrase = process.argv[3];
    const objUuid = process.argv[4];

    const storage = new EncryptedStorage(dbPath);
    await storage.unlockDatabase(passphrase);

    const payload = storage.retrievePayload(objUuid);
    console.log(JSON.stringify(payload));
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
