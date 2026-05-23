const fs = require('fs');
const path = require('path');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');
const cryptoUtils = require('../src/crypto');
let initSqlJs;

describe('V1 Metadata tests (Browser)', () => {
    beforeAll(async () => {
        initSqlJs = require('sql.js');
    });

    it('should throw InvalidStorageFormat when metadata property is missing', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        storage.db.exec("DELETE FROM storage_metadata_tbl WHERE property = 'format_major'");

        await expect(storage.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should throw InvalidStorageFormat on invalid created_at_ms format', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        storage.db.exec("UPDATE storage_metadata_tbl SET value = 'abc' WHERE property = 'created_at_ms'");

        await expect(storage.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should throw InvalidStorageFormat on non-canonical JCS features', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        storage.db.exec("UPDATE storage_metadata_tbl SET value = '[ ]' WHERE property = 'required_features'");

        await expect(storage.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should prioritize StorageClosed over other errors', async () => {
        const storage = new EncryptedStorage();
        await storage.init();
        await storage.close();

        await expect(storage.unlockDatabase(123)).rejects.toThrow(errors.StorageClosed);
        await expect(storage.initializeDatabase(123, "web")).rejects.toThrow(errors.StorageClosed);
    });

    it('should throw InvalidPassphrase for non-string', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await expect(storage.initializeDatabase(123, "web")).rejects.toThrow(errors.InvalidPassphrase);

        await storage.initializeDatabase("pass", "web");
        await expect(storage.unlockDatabase(123)).rejects.toThrow(errors.InvalidPassphrase);
    });

    it('should prioritize InvalidStorageFormat on already initialized check if missing KEK', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        storage.db.exec("PRAGMA foreign_keys = OFF; DELETE FROM key_tbl WHERE key_class = 'database_kek'");

        const exported = storage.db.export();
        await storage.close();

        let storage2 = new EncryptedStorage();
        await storage2.init(exported);

        await expect(storage2.initializeDatabase("pass", "web")).rejects.toThrow(/missing KEK/);
    });

    it('should throw InvalidStorageFormat for unknown required features', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        storage.db.exec(`UPDATE storage_metadata_tbl SET value = '["unknown"]' WHERE property = 'required_features'`);

        await expect(storage.unlockDatabase("pass")).rejects.toThrow(/Unknown required features/);
    });

    it('should throw InvalidStorageFormat for invalid provider config explicit mismatch', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        const res = storage.db.exec("SELECT kid, provider_config_json FROM unlock_kek_tbl LIMIT 1");
        const row = res[0].values[0];
        const config = JSON.parse(row[1]);
        config.profile = "argon2id-profile-v2";
        const nonCanonical = cryptoUtils.canonicalizeJson(config).toString('utf-8');
        storage.db.run(`UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?`, [nonCanonical, row[0]]);

        const exported = storage.db.export();
        await storage.close();

        let storage2 = new EncryptedStorage();
        await storage2.init(exported);

        await expect(storage2.unlockDatabase("pass")).rejects.toThrow(/Unknown or missing profile in provider_config_json/);
    });

    it('should throw InvalidStorageFormat for non JCS canonical provider config', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        const res = storage.db.exec("SELECT kid, provider_config_json FROM unlock_kek_tbl LIMIT 1");
        const row = res[0].values[0];
        const config = JSON.parse(row[1]);
        const nonCanonical = JSON.stringify(config, null, 2);
        storage.db.run(`UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?`, [nonCanonical, row[0]]);

        const exported = storage.db.export();
        await storage.close();

        let storage2 = new EncryptedStorage();
        await storage2.init(exported);

        await expect(storage2.unlockDatabase("pass")).rejects.toThrow(/provider_config_json is not JCS canonical/);
    });

    it('should enforce SQLite constraints', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        // sql.js should throw on CHECK constraint
        const kid = "00000000-0000-1000-8000-000000000000";
        storage.db.run(`INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES ('${kid}', 'record_dek', 'encrypt_payload', 'A256GCM', 'active', 0)`);

        expect(() => {
            storage.db.run(`INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES ('11111111-1111-1111-8111-111111111111', 1, 'aead', '${kid}', '', 'A256GCM', '${kid}', x'000000000000000000000000', x'00000000000000000000000000000000', 'policy', 0, 0)`);
        }).toThrow(/CHECK constraint failed/);

        expect(() => {
            storage.db.run(`INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES ('11111111-1111-1111-8111-111111111111', 1, 'aead', '${kid}', 'a/b', 'A256GCM', '${kid}', x'00', x'00000000000000000000000000000000', 'policy', 0, 0)`);
        }).toThrow(/CHECK constraint failed/);
    });

});