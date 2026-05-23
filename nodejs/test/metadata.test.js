const fs = require('fs');
const path = require('path');
const os = require('os');
const Database = require('better-sqlite3');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');
const cryptoUtils = require('../src/crypto');

describe('Metadata V1 Validation', () => {
    let dbPath;

    beforeEach(() => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'metadata-test-'));
        dbPath = path.join(tempDir, 'test.db');
    });

    afterEach(() => {
        if (fs.existsSync(dbPath)) {
            fs.unlinkSync(dbPath);
        }
        const tempDir = path.dirname(dbPath);
        if (fs.existsSync(tempDir)) {
            fs.rmdirSync(tempDir);
        }
    });

    it('should create valid metadata on initialization', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");

        const db = new Database(dbPath);
        const rows = db.prepare("SELECT property, value FROM storage_metadata_tbl").all();
        const meta = {};
        for (const row of rows) meta[row.property] = row.value;

        expect(meta.storage_format_id).toBe("vault.moukaeritai.work.storage");
        expect(meta.format_major).toBe("1");
        expect(meta.format_minor).toBe("0");
        expect(meta.schema_version).toBe("1");
        expect(meta.created_by_library).toBe("nodejs");
        expect(meta.created_by_version).toBe("0.0.0-dev");
        expect(meta.sqlite_application_id).toBe("1447906135");
        expect(meta.sqlite_user_version).toBe("1");
        expect(meta.database_uuid).toBeDefined();
        expect(/^[0-9]+$/.test(meta.created_at_ms)).toBe(true);
        expect(meta.required_features).toBe("[]");
        expect(meta.optional_features).toBe("[]");

        const appId = db.pragma("application_id", { simple: true });
        expect(String(appId)).toBe("1447906135");

        db.close();
        storage.close();
    });

    it('should reject invalid metadata format_major', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("UPDATE storage_metadata_tbl SET value = '2' WHERE property = 'format_major'").run();
        db.close();

        const storage2 = new EncryptedStorage(dbPath);
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject missing metadata property', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("DELETE FROM storage_metadata_tbl WHERE property = 'database_uuid'").run();
        db.close();

        const storage2 = new EncryptedStorage(dbPath);
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject invalid feature', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("UPDATE storage_metadata_tbl SET value = '[\"unknown_feature\"]' WHERE property = 'required_features'").run();
        db.close();

        const storage2 = new EncryptedStorage(dbPath);
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject invalid jcs feature', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("UPDATE storage_metadata_tbl SET value = '[ ]' WHERE property = 'required_features'").run();
        db.close();

        const storage2 = new EncryptedStorage(dbPath);
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject invalid provider config', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        const row = db.prepare("SELECT kid, provider_config_json FROM unlock_kek_tbl WHERE unlock_provider = 'passphrase_argon2id'").get();
        const config = JSON.parse(row.provider_config_json);
        config.kdf = "pbkdf2";

        const canonicalConfig = cryptoUtils.canonicalizeJson(config).toString('utf-8');
        db.prepare("UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?").run(canonicalConfig, row.kid);
        db.close();

        const storage2 = new EncryptedStorage(dbPath);
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should enforce error precedence', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");
        storage.close();

        // 1. Closed storage + invalid arg -> StorageClosed
        await expect(storage.unlockDatabase(123)).rejects.toThrow(errors.StorageClosed);

        const storage2 = new EncryptedStorage(dbPath);
        // 2. Open storage + invalid arg -> InvalidPassphrase
        await expect(storage2.unlockDatabase(123)).rejects.toThrow(errors.InvalidPassphrase);

        // 3. Open storage + wrong arg -> UnlockFailed
        await expect(storage2.unlockDatabase("wrong")).rejects.toThrow(errors.UnlockFailed);
    });
});
