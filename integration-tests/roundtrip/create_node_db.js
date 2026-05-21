const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');

// Ensure the library can be found
const EncryptedStorage = require('../../nodejs/src/storage');

async function main() {
    if (process.argv.length < 3) {
        console.error("Usage: node create_node_db.js <db_path>");
        process.exit(1);
    }

    const dbPath = process.argv[2];

    if (fs.existsSync(dbPath)) {
        fs.unlinkSync(dbPath);
    }

    const storage = new EncryptedStorage(dbPath);
    const conn = storage.conn;

    const schemaSql = fs.readFileSync(path.resolve(__dirname, '../../docs/backend/sqlite/schema.sql'), 'utf8');
    conn.exec(schemaSql);

    // Pre-populate platform table as per schema requirements
    conn.prepare("INSERT INTO platform_tbl (platform, description) VALUES ('integration_test_platform', 'Integration Test Platform')").run();

    await storage.initializeDatabase("fixed_passphrase", "integration_test_platform");

    const payload = {hello: "world", source: "nodejs"};
    const schemaUuid = "00000000-0000-4000-8000-000000000002";

    const objectUuid = await storage.storePayload(schemaUuid, "application/json", payload);

    // Print the UUID to stdout so it can be captured
    console.log(objectUuid);

    storage.close();
}

main().catch(err => {
    console.error(err);
    process.exit(1);
});
