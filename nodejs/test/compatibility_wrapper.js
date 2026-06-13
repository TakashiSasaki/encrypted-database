const fs = require('fs');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');

async function main() {
    const args = process.argv.slice(2);
    let operation = null;
    let dbPath = null;
    let schemaUuid = null;
    let contentType = null;
    let objectUuid = null;

    if (args.length > 0 && !args[0].startsWith('--')) {
        operation = args[0];
    }

    for (let i = 0; i < args.length; i++) {
        if (args[i] === '--db' && i + 1 < args.length) dbPath = args[++i];
        if (args[i] === '--schema' && i + 1 < args.length) schemaUuid = args[++i];
        if (args[i] === '--content-type' && i + 1 < args.length) contentType = args[++i];
        if (args[i] === '--object-uuid' && i + 1 < args.length) objectUuid = args[++i];
    }

    if (!operation || (operation !== 'write' && operation !== 'read') || !dbPath || !schemaUuid || !contentType) {
        console.log(JSON.stringify({ok: false, operation: operation || "unknown", error: "Missing required arguments"}));
        process.exit(1);
    }

    const passphrase = process.env.VAULT_PASSPHRASE;
    if (!passphrase) {
        console.log(JSON.stringify({ok: false, operation, error: "VAULT_PASSPHRASE environment variable is required"}));
        process.exit(1);
    }

    try {
        const storage = new EncryptedStorage(dbPath);

        if (operation === 'write') {
            const status = storage.getStatus();
            if (status === 'uninitialized') {
                await storage.initializeDatabase(passphrase, "linux"); // Using dummy platform
            } else {
                await storage.unlockDatabase(passphrase);
            }

            const payloadStr = fs.readFileSync(0, 'utf-8');
            let payload;
            try {
                payload = JSON.parse(payloadStr);
            } catch(e) {
                console.log(JSON.stringify({ok: false, operation, error: "Invalid JSON payload"}));
                process.exit(1);
            }

            const storedObjectUuid = storage.storePayload(schemaUuid, contentType, payload);
            storage.close();

            console.log(JSON.stringify({
                ok: true,
                operation: "write",
                object_uuid: storedObjectUuid
            }));

        } else if (operation === 'read') {
            if (!objectUuid) {
                console.log(JSON.stringify({ok: false, operation, error: "--object-uuid is required for read operation"}));
                process.exit(1);
            }

            await storage.unlockDatabase(passphrase);
            const payload = storage.retrievePayload(objectUuid);
            storage.close();

            console.log(JSON.stringify({
                ok: true,
                operation: "read",
                payload: payload
            }));
        }

    } catch (e) {
        console.log(JSON.stringify({
            ok: false,
            operation,
            error: e.message || String(e)
        }));
        process.exit(1);
    }
}

main().catch(err => {
    console.log(JSON.stringify({
        ok: false,
        operation: "unknown",
        error: String(err)
    }));
    process.exit(1);
});
