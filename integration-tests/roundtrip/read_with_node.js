const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

// Ensure the library can be found
const EncryptedStorage = require('../../nodejs/src/storage');

async function main() {
    if (process.argv.length < 4) {
        console.error("Usage: node read_with_node.js <db_path> <object_uuid>");
        process.exit(1);
    }

    const dbPath = process.argv[2];
    const objectUuid = process.argv[3];

    if (!fs.existsSync(dbPath)) {
        console.error(`Database not found at ${dbPath}`);
        process.exit(1);
    }

    const storage = new EncryptedStorage(dbPath);

    await storage.unlockDatabase("fixed_passphrase");

    const payload = storage.retrievePayload(objectUuid);

    if (payload.hello === "world" && payload.source === "python") {
        console.log("SUCCESS");
    } else {
        console.error("Payload mismatch:", payload);
        process.exit(1);
    }

    storage.close();
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
