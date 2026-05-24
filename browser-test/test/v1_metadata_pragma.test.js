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
        const props = [
            "storage_format_id", "format_major", "format_minor", "schema_version",
            "database_uuid", "created_at_ms", "created_by_library", "created_by_version",
            "sqlite_application_id", "sqlite_user_version",
            "required_features", "optional_features"
        ];

        for (const prop of props) {
            let storage = new EncryptedStorage();
            await storage.init();
            await storage.initializeDatabase("pass", "web");

            storage.db.run(`DELETE FROM storage_metadata_tbl WHERE property = ?`, [prop]);

            const exported = storage.db.export();
            await storage.close();

            let storage2 = new EncryptedStorage();
            await storage2.init(exported);
            try {
                await expect(storage2.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage2.close();
            }
        }
    });

    it('should throw InvalidStorageFormat on metadata value mismatch', async () => {
        const mutations = [
            { prop: "storage_format_id", value: "vault.moukaeritai.work.storage.invalid" },
            { prop: "format_major", value: "2" },
            { prop: "format_minor", value: "1" },
            { prop: "schema_version", value: "2" },
            { prop: "sqlite_application_id", value: "1234567890" },
            { prop: "sqlite_user_version", value: "2" }
        ];

        for (const mutation of mutations) {
            let storage = new EncryptedStorage();
            await storage.init();
            await storage.initializeDatabase("pass", "web");

            storage.db.run(`UPDATE storage_metadata_tbl SET value = ? WHERE property = ?`, [mutation.value, mutation.prop]);

            const exported = storage.db.export();
            await storage.close();

            let storage2 = new EncryptedStorage();
            await storage2.init(exported);
            try {
                await expect(storage2.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage2.close();
            }
        }
    });

    it('should throw InvalidStorageFormat on invalid created_at_ms format', async () => {
        const invalidCases = ["", "-1", "+1", "1.0", "1e3", " 123", "123 ", "abc", "001", "00"];

        for (const invalidVal of invalidCases) {
            let storage = new EncryptedStorage();
            await storage.init();
            await storage.initializeDatabase("pass", "web");

            storage.db.run(`UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_at_ms'`, [invalidVal]);

            const exported = storage.db.export();
            await storage.close();

            let storage2 = new EncryptedStorage();
            await storage2.init(exported);
            try {
                await expect(storage2.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage2.close();
            }
        }
    });

    it('should throw InvalidStorageFormat on invalid created_by_library and created_by_version', async () => {
        const invalidCases = ["", "   ", "\t\n"];

        for (const invalidVal of invalidCases) {
            let storage = new EncryptedStorage();
            await storage.init();
            await storage.initializeDatabase("pass", "web");

            storage.db.run(`UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_by_library'`, [invalidVal]);

            const exported = storage.db.export();
            await storage.close();

            let storage2 = new EncryptedStorage();
            await storage2.init(exported);
            try {
                await expect(storage2.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage2.close();
            }

            let storage3 = new EncryptedStorage();
            await storage3.init();
            await storage3.initializeDatabase("pass", "web");

            storage3.db.run(`UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_by_version'`, [invalidVal]);

            const exported3 = storage3.db.export();
            await storage3.close();

            let storage4 = new EncryptedStorage();
            await storage4.init(exported3);
            try {
                await expect(storage4.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage4.close();
            }
        }
    });

    it('provenance not compatibility gate', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        storage.db.run(`UPDATE storage_metadata_tbl SET value = 'some-other-implementation' WHERE property = 'created_by_library'`);
        storage.db.run(`UPDATE storage_metadata_tbl SET value = '9.9.9-test' WHERE property = 'created_by_version'`);

        const exported = storage.db.export();
        await storage.close();

        let storage2 = new EncryptedStorage();
        await storage2.init(exported);
        await storage2.unlockDatabase("pass");
        expect(storage2.activeDbKek).toBeDefined();
        await storage2.close();
    });

    it('should throw InvalidStorageFormat on invalid jcs features flags', async () => {
        const invalidCases = ["{}", '""', '"[]"', "null", "123", "0", "true", "false", "[1]", "[\"unknown_feature\"]", "[ ]", "[\n]", "[ \n\t]", "invalid"];

        for (const invalidVal of invalidCases) {
            let storage = new EncryptedStorage();
            await storage.init();
            await storage.initializeDatabase("pass", "web");

            storage.db.run(`UPDATE storage_metadata_tbl SET value = ? WHERE property = 'required_features'`, [invalidVal]);

            const exported = storage.db.export();
            await storage.close();

            let storage2 = new EncryptedStorage();
            await storage2.init(exported);
            try {
                await expect(storage2.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage2.close();
            }

            let storage3 = new EncryptedStorage();
            await storage3.init();
            await storage3.initializeDatabase("pass", "web");

            storage3.db.run(`UPDATE storage_metadata_tbl SET value = ? WHERE property = 'optional_features'`, [invalidVal]);

            const exported3 = storage3.db.export();
            await storage3.close();

            let storage4 = new EncryptedStorage();
            await storage4.init(exported3);
            try {
                await expect(storage4.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage4.close();
            }
        }
    });

    it('should throw InvalidStorageFormat for invalid provider config explicit mismatch', async () => {
        const modifiers = [
            c => { delete c.profile; return c; },
            c => { c.profile = "argon2id-profile-v2"; return c; },
            c => { c.kdf = "pbkdf2"; return c; },
            c => { c.memory_kib = 1024; return c; },
            c => { c.iterations = 4; return c; },
            c => { c.parallelism = 2; return c; },
            c => { c.output_bytes = 16; return c; },
            c => { delete c.salt; return c; },
            c => { c.salt += "="; return c; },
            c => { c.salt = "invalid+salt/char"; return c; },
            c => { c.salt = "MTIzNDU2Nzg5MDEyMzQ1"; return c; },
            c => '{ "profile": "argon2id-profile-v1", "kdf": "argon2id" }'
        ];

        for (const mod of modifiers) {
            let storage = new EncryptedStorage();
            await storage.init();
            await storage.initializeDatabase("pass", "web");

            const res = storage.db.exec("SELECT kid, provider_config_json FROM unlock_kek_tbl WHERE unlock_provider = 'passphrase_argon2id'");
            const row = res[0].values[0];
            const config = JSON.parse(row[1]);

            const newConfig = mod(config);
            let canonicalConfig;
            if (typeof newConfig === 'string') {
                canonicalConfig = newConfig;
            } else {
                canonicalConfig = cryptoUtils.canonicalizeJson(newConfig).toString('utf-8');
            }

            storage.db.run(`UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?`, [canonicalConfig, row[0]]);

            const exported = storage.db.export();
            await storage.close();

            let storage2 = new EncryptedStorage();
            await storage2.init(exported);
            try {
                await expect(storage2.unlockDatabase("pass")).rejects.toThrow(errors.InvalidStorageFormat);
            } finally {
                await storage2.close();
            }
        }
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

    it('should throw UnlockFailed for wrong passphrase', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");
        const exported = storage.db.export();
        await storage.close();

        let storage2 = new EncryptedStorage();
        await storage2.init(exported);
        await expect(storage2.unlockDatabase("wrong")).rejects.toThrow(errors.UnlockFailed);
    });

    it('should prioritize InvalidStorageFormat over UnlockFailed for bad metadata', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");
        storage.db.run("UPDATE storage_metadata_tbl SET value = 'invalid' WHERE property = 'format_major'");
        const exported = storage.db.export();
        await storage.close();

        let storage2 = new EncryptedStorage();
        await storage2.init(exported);
        await expect(storage2.unlockDatabase("wrong")).rejects.toThrow(errors.InvalidStorageFormat);
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

    it('should throw InvalidStorageFormat for non JCS canonical provider config', async () => {
        let storage = new EncryptedStorage();
        await storage.init();
        await storage.initializeDatabase("pass", "web");

        const res = storage.db.exec("SELECT kid, provider_config_json FROM unlock_kek_tbl WHERE unlock_provider = 'passphrase_argon2id'");
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

    // --- Documented Exceptions for Browser / sql.js environments ---

    it.skip('malformed provider_config_json corruption via ignore_check_constraints is not required in browser-test/sql.js', async () => {
        // sql.js/browser-test does not rely on PRAGMA ignore_check_constraints for conformance.
        // Python and Node.js file-backed SQLite cover malformed-on-disk corruption.
        // Browser-test covers semantic invalid JSON and JCS validation instead.
    });

    it.skip('PRAGMA application_id / user_version validation is skipped in browser-test/sql.js', async () => {
        // sql.js/browser-test skips PRAGMA application_id and PRAGMA user_version validations
        // because these PRAGMAs do not reliably persist across in-memory database export/import serializations.
        // The storage_metadata_tbl is treated as the sole authoritative source.
    });

});
