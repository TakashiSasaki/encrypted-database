const fs = require('fs');
const path = require('path');
const { canonicalize } = require('../../nodejs/node_modules/json-canonicalize');

const EncryptedStorage = require('../../nodejs/src/storage');

async function main() {
    if (process.argv.length < 4) {
        console.error("Usage: node generate_fixture_node.js <db_path> <env_out_path>");
        process.exit(1);
    }

    const dbPath = process.argv[2];
    const envOutPath = process.argv[3];
    const passphrase = "fixture-passphrase-node";

    if (fs.existsSync(dbPath)) {
        fs.unlinkSync(dbPath);
    }

    const storage = new EncryptedStorage(dbPath);
    try {
        await storage.initializeDatabase(passphrase, "linux");

        const schemaUuid = "00000000-0000-4000-8000-000000000001";
        const contentType = "application/json";
        const payload = {
            "secret": "cross-language-fixture",
            "value": 42,
            "nested": {
                "ok": true
            },
            "items": ["nodejs", "go", "rust"]
        };

        const objUuid = await storage.storePayload(schemaUuid, contentType, payload);

        // Convert the object to JCS string then to bytes to hex
        const jcsString = canonicalize(payload);
        const expectedPayloadHex = Buffer.from(jcsString, 'utf8').toString('hex');

        const envContent = `VAULT_SQLITE_V1_FIXTURE_DB="${dbPath}"
VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="${passphrase}"
VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="${objUuid}"
VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="${expectedPayloadHex}"
`;

        fs.writeFileSync(envOutPath, envContent);

    } finally {
        storage.close();
    }
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
