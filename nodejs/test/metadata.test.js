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

    let activeStorages = [];

    afterEach(() => {
        for (const storage of activeStorages) {
            try { storage.close(); } catch (e) {}
        }
        activeStorages = [];
        if (fs.existsSync(dbPath)) {
            try { fs.unlinkSync(dbPath); } catch (e) {}
        }
        const tempDir = path.dirname(dbPath);
        if (fs.existsSync(tempDir)) {
            try { fs.rmdirSync(tempDir); } catch (e) {}
        }
    });

    it('should create valid metadata on initialization', async () => {
        const storage = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
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
        const storage = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("UPDATE storage_metadata_tbl SET value = '2' WHERE property = 'format_major'").run();
        db.close();

        const storage2 = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject missing metadata property', async () => {
        const storage = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("DELETE FROM storage_metadata_tbl WHERE property = 'database_uuid'").run();
        db.close();

        const storage2 = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject invalid feature', async () => {
        const storage = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("UPDATE storage_metadata_tbl SET value = '[\"unknown_feature\"]' WHERE property = 'required_features'").run();
        db.close();

        const storage2 = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject invalid jcs feature', async () => {
        const storage = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        db.prepare("UPDATE storage_metadata_tbl SET value = '[ ]' WHERE property = 'required_features'").run();
        db.close();

        const storage2 = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should reject invalid provider config', async () => {
        const storage = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await storage.initializeDatabase("password", "linux");
        storage.close();

        const db = new Database(dbPath);
        const row = db.prepare("SELECT kid, provider_config_json FROM unlock_kek_tbl WHERE unlock_provider = 'passphrase_argon2id'").get();
        const config = JSON.parse(row.provider_config_json);
        config.kdf = "pbkdf2";

        const canonicalConfig = cryptoUtils.canonicalizeJson(config).toString('utf-8');
        db.prepare("UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?").run(canonicalConfig, row.kid);
        db.close();

        const storage2 = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
    });

    it('should enforce error precedence', async () => {
        const storage = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        await storage.initializeDatabase("password", "linux");
        storage.close();

        // 1. Closed storage + invalid arg -> StorageClosed
        await expect(storage.unlockDatabase(123)).rejects.toThrow(errors.StorageClosed);

        const storage2 = (() => { const s = new EncryptedStorage(dbPath); activeStorages.push(s); return s; })();
        // 2. Open storage + invalid arg -> InvalidPassphrase
        await expect(storage2.unlockDatabase(123)).rejects.toThrow(errors.InvalidPassphrase);

        // 3. Open storage + wrong arg -> UnlockFailed
        await expect(storage2.unlockDatabase("wrong")).rejects.toThrow(errors.UnlockFailed);
    });

    async function withFreshInitializedDb(testFn) {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'metadata-test-'));
        const dbPath = path.join(tempDir, 'test.db');
        let storage = null;
        let rawDb = null;

        try {
            storage = new EncryptedStorage(dbPath);
            await storage.initializeDatabase('password', 'linux');

            await testFn({
                dbPath,
                storage,
                closeStorage: () => {
                    if (storage && !storage._isClosed) {
                        storage.close();
                    }
                    storage = null;
                },
                openRawDb: () => {
                    rawDb = new Database(dbPath);
                    return rawDb;
                },
                reopenStorage: () => new EncryptedStorage(dbPath),
            });
        } finally {
            if (rawDb) {
                try { rawDb.close(); } catch (_) {}
            }
            if (storage && !storage._isClosed) {
                try { storage.close(); } catch (_) {}
            }
            if (fs.existsSync(dbPath)) {
                try { fs.unlinkSync(dbPath); } catch (_) {}
            }
            if (fs.existsSync(tempDir)) {
                try { fs.rmdirSync(tempDir); } catch (_) {}
            }
        }
    }

    test('invalid created_at_ms format', async () => {
        const invalidCases = ["", "-1", "+1", "1.0", "1e3", " 123", "123 ", "abc", "001", "00"];
        for (const invalidVal of invalidCases) {
            await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
                closeStorage();
                const conn = openRawDb();
                conn.prepare("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_at_ms'").run(invalidVal);
                conn.close();
                const storage2 = reopenStorage();
                await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
                storage2.close();
            });
        }
    });

    test('invalid created_by_library and created_by_version', async () => {
        const invalidCases = ["", "   ", "\t\n"];
        for (const invalidVal of invalidCases) {
            await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
                closeStorage();
                const conn = openRawDb();
                conn.prepare("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_by_library'").run(invalidVal);
                conn.close();
                const storage2 = reopenStorage();
                await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
                storage2.close();
            });
            await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
                closeStorage();
                const conn = openRawDb();
                conn.prepare("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_by_version'").run(invalidVal);
                conn.close();
                const storage2 = reopenStorage();
                await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
                storage2.close();
            });
        }
    });

    test('missing metadata table or empty', async () => {
        await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
            closeStorage();
            const conn = openRawDb();
            conn.prepare("DELETE FROM storage_metadata_tbl").run();
            conn.close();
            const storage2 = reopenStorage();
            await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
            storage2.close();
        });
        await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
            closeStorage();
            const conn = openRawDb();
            conn.prepare("DROP TABLE storage_metadata_tbl").run();
            conn.close();
            const storage2 = reopenStorage();
            await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
            storage2.close();
        });
    });

    test('feature flags validation', async () => {
        const invalidCases = ["{}", '""', '"[]"', "null", "123", "0", "true", "false", "[1]", "[\"unknown_feature\"]", "[ ]", "[\n]", "[ \n\t]", "invalid"];

        for (const invalidVal of invalidCases) {
            await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
                closeStorage();
                const conn = openRawDb();
                conn.prepare("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'required_features'").run(invalidVal);
                conn.close();
                const storage2 = reopenStorage();
                await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
                storage2.close();
            });

            await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
                closeStorage();
                const conn = openRawDb();
                conn.prepare("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'optional_features'").run(invalidVal);
                conn.close();
                const storage2 = reopenStorage();
                await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
                storage2.close();
            });
        }
    }, 15000);

    test('PRAGMA validation', async () => {
        await withFreshInitializedDb(async ({ closeStorage, openRawDb }) => {
            closeStorage();
            const conn = openRawDb();
            let appId = conn.pragma("application_id", { simple: true });
            expect(appId).toBe(1447906135);
            let userVersion = conn.pragma("user_version", { simple: true });
            expect(userVersion).toBe(1);
        });

        await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
            closeStorage();
            const conn = openRawDb();
            conn.pragma("application_id = 0");
            conn.close();
            const storage2 = reopenStorage();
            await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
            storage2.close();
        });

        await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
            closeStorage();
            const conn = openRawDb();
            conn.pragma("application_id = 1447906135");
            conn.pragma("user_version = 2");
            conn.close();
            const storage3 = reopenStorage();
            await expect(storage3.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
            storage3.close();
        });
    });

    test('invalid provider config combinations', async () => {
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
            await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
                closeStorage();
                const db = openRawDb();
                const row = db.prepare("SELECT kid, provider_config_json FROM unlock_kek_tbl WHERE unlock_provider = 'passphrase_argon2id'").get();
                const config = JSON.parse(row.provider_config_json);

                const newConfig = mod(config);
                let canonicalConfig;
                if (typeof newConfig === 'string') {
                    canonicalConfig = newConfig;
                } else {
                    canonicalConfig = cryptoUtils.canonicalizeJson(newConfig).toString('utf-8');
                }

                db.prepare("UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?").run(canonicalConfig, row.kid);
                db.close();

                const storage2 = reopenStorage();
                await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
                storage2.close();
            });
        }

        // Malformed JSON (corruption test bypassing CHECK constraints)
        await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
            closeStorage();
            const db = openRawDb();
            db.pragma('ignore_check_constraints = ON');
            db.prepare("UPDATE unlock_kek_tbl SET provider_config_json = '{ malformed' WHERE unlock_provider = 'passphrase_argon2id'").run();
            db.pragma('ignore_check_constraints = OFF');
            db.close();

            const storage2 = reopenStorage();
            await expect(storage2.unlockDatabase("password")).rejects.toThrow(errors.InvalidStorageFormat);
            storage2.close();
        });
    }, 15000);

    test('provenance not compatibility gate', async () => {
        await withFreshInitializedDb(async ({ closeStorage, openRawDb, reopenStorage }) => {
            closeStorage();
            const conn = openRawDb();
            conn.prepare("UPDATE storage_metadata_tbl SET value = 'some-other-implementation' WHERE property = 'created_by_library'").run();
            conn.prepare("UPDATE storage_metadata_tbl SET value = '9.9.9-test' WHERE property = 'created_by_version'").run();
            conn.close();

            const storage2 = reopenStorage();
            await storage2.unlockDatabase("password");
            expect(storage2.activeDbKek).toBeDefined();
            storage2.close();
        });
    });

});
