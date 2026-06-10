const path = require('path');
const fs = require('fs');

let EncryptedStorage;
let cryptoUtils;
try {
    const storageMod = require('../../nodejs/src/storage');
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
    if (process.argv.length < 9) {
        console.error("Usage: node write_matrix_fixture_node.js <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a_json> <payload_b_json> [mode:update_only|update_delete]");
        process.exit(1);
    }

    const dbPath = process.argv[2];
    const passphrase = process.argv[3];
    const platform = process.argv[4];
    const schemaUuid = process.argv[5];
    const contentType = process.argv[6];
    const payloadAJson = process.argv[7];
    const payloadBJson = process.argv[8];

    let mode = "update_delete";
    if (process.argv.length >= 10) {
        mode = process.argv[9];
    }

    // V1 Writers from python/node ignore VAULT_SCHEMA_SQL_PATH normally.

    if (fs.existsSync(dbPath)) {
        console.error(`Error: Database file already exists at ${dbPath}`);
        process.exit(1);
    }

    let payloadA, payloadB;
    try {
        payloadA = JSON.parse(payloadAJson);
        payloadB = JSON.parse(payloadBJson);
    } catch (e) {
        console.error(`Error parsing JSON payload: ${e.message}`);
        process.exit(1);
    }

    let storage;
    try {
        storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase(passphrase, platform);

        const objectUuid = storage.storePayload(schemaUuid, contentType, payloadA);
        storage.updatePayload(objectUuid, schemaUuid, contentType, payloadB);

        let deleted = false;
        if (mode === "update_delete") {
            storage.deletePayload(objectUuid);
            deleted = true;
        }

        const initialHex = cryptoUtils.canonicalizeJson(payloadA).toString('hex').toLowerCase();
        const updatedHex = cryptoUtils.canonicalizeJson(payloadB).toString('hex').toLowerCase();

        const output = {
            object_uuid: objectUuid,
            initial_payload_hex: initialHex,
            updated_payload_hex: updatedHex,
            deleted: deleted
        };

        console.log(JSON.stringify(output));

    } catch (e) {
        console.error(`Error during Node.js write: ${e.message}`);
        process.exit(1);
    } finally {
        if (storage) {
            storage.close();
        }
    }
}

main();
