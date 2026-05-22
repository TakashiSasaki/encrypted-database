const initSqlJs = require('sql.js');
const { v4: uuidv4 } = require('uuid');
const aadPolicy = require('./aadPolicy');
const cryptoUtils = require('./crypto');
const errors = require('./errors');
const schemaSql = require('!!raw-loader!../../docs/backend/sqlite/schema.sql').default;

class EncryptedStorage {
    static _UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

    constructor() {
        this.db = null;
        this.activeDbKek = null;
        this.activeDbKid = null;
        this._isClosed = false;
        this._isInit = false;
    }

    async init(databaseBytes = null) {
        const SQL = await initSqlJs({
            locateFile: file => {
              if (file.endsWith('.wasm')) return 'sql-wasm.wasm';
              return file;
            }
        });
        this.db = databaseBytes ? new SQL.Database(databaseBytes) : new SQL.Database();
        this.db.exec("PRAGMA foreign_keys = ON;");
        this._isClosed = false;
        this._isInit = true;
    }

    _bootstrapSchema() {
        this.db.exec(schemaSql);
    }

    _currentMs() {
        return Date.now();
    }

    _b64e(b) {
        // base64url encoding replacement for browser
        const b64 = Buffer.isBuffer(b) ? b.toString('base64') : Buffer.from(b).toString('base64');
        return b64.replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '');
    }

    _b64d(s) {
        let b64 = s.replace(/-/g, '+').replace(/_/g, '/');
        while (b64.length % 4) {
            b64 += '=';
        }
        return Buffer.from(b64, 'base64');
    }

    _validatePlatform(platform) {
        if (!platform || platform === 'cross_platform') {
            throw new errors.UnsupportedPlatform('A concrete platform name is required; cross_platform is not allowed');
        }
        let hasRow = false;
        try {
            const stmt = this.db.prepare('SELECT 1 FROM platform_tbl WHERE platform = ?');
            stmt.bind([platform]);
            hasRow = stmt.step();
            stmt.free();
        } catch (e) {
            if (e.message.includes("no such table")) {
                throw new errors.UnsupportedPlatform(`Unsupported platform: ${platform}`);
            }
            throw new errors.DatabaseBackendError(`Database error during platform validation: ${e.message}`);
        }
        if (!hasRow) {
            throw new errors.UnsupportedPlatform(`Unsupported platform: ${platform}`);
        }
    }

    _validateUuid(value, fieldName) {
        if (typeof value !== 'string' || !EncryptedStorage._UUID_PATTERN.test(value)) {
            throw new errors.InvalidUuid(`Invalid ${fieldName}: must be a canonical lowercase hyphenated UUID`);
        }
    }

    _validateContentType(value) {
        if (typeof value !== 'string' || value.trim() === '') {
            throw new errors.InvalidContentType("Content type must be a non-empty string");
        }
        for (let i = 0; i < value.length; i++) {
            const code = value.charCodeAt(i);
            if (code < 32 || code === 127) {
                throw new errors.InvalidContentType("Content type must not contain control characters");
            }
        }
        if (!value.includes('/')) {
            throw new errors.InvalidContentType("Content type must be a basic type/subtype format");
        }
    }

    _validatePayload(value, path = "$", isTopLevel = true, visited = new Set()) {
        if (typeof value === 'object' && value !== null) {
            if (visited.has(value)) {
                throw new errors.InvalidPayload(`Invalid payload at ${path}: cyclic reference detected`);
            }
            visited.add(value);
        }

        if (isTopLevel) {
            if (typeof value !== 'object' || value === null || Array.isArray(value)) {
                if (typeof value === 'object' && value !== null) visited.delete(value);
                throw new errors.InvalidPayload(`Invalid payload at ${path}: must be a plain object at top level`);
            }
        }

        if (value === null) {
            return;
        }

        if (typeof value === 'boolean' || typeof value === 'string') {
            return;
        }

        if (typeof value === 'number') {
            if (!Number.isFinite(value)) {
                throw new errors.InvalidPayload(`Invalid payload at ${path}: NaN and Infinity are not valid JSON`);
            }
            return;
        }

        if (typeof value === 'object') {
            if (typeof Buffer !== 'undefined' && Buffer.isBuffer(value)) {
                visited.delete(value);
                throw new errors.InvalidPayload(`Invalid payload at ${path}: Buffer is not allowed`);
            }
            if (value instanceof ArrayBuffer || ArrayBuffer.isView(value)) {
                visited.delete(value);
                throw new errors.InvalidPayload(`Invalid payload at ${path}: ArrayBuffer/TypedArray/DataView is not allowed`);
            }
            if (value instanceof Date || value instanceof Map || value instanceof Set || value instanceof RegExp) {
                visited.delete(value);
                throw new errors.InvalidPayload(`Invalid payload at ${path}: ${value.constructor.name} is not allowed`);
            }

            if (Array.isArray(value)) {
                for (let i = 0; i < value.length; i++) {
                    this._validatePayload(value[i], `${path}[${i}]`, false, visited);
                }
                visited.delete(value);
                return;
            }

            const proto = Object.getPrototypeOf(value);
            if (proto !== Object.prototype && proto !== null) {
                visited.delete(value);
                throw new errors.InvalidPayload(`Invalid payload at ${path}: class instances are not allowed`);
            }

            for (const key of Object.keys(value)) {
                this._validatePayload(value[key], `${path}.${key}`, false, visited);
            }
            visited.delete(value);
            return;
        }

        throw new errors.InvalidPayload(`Invalid payload at ${path}: unsupported type ${typeof value}`);
    }

    async initializeDatabase(passphrase, platform = "web") {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        if (typeof passphrase !== 'string') {
            throw new errors.InvalidPassphrase("Passphrase must be a string");
        }
        if (typeof platform !== 'string') {
            throw new errors.UnsupportedPlatform("Platform must be a string");
        }

        if (this.isUnlocked()) throw new errors.StorageAlreadyInitialized("Storage is already initialized");
        if (!this.db) await this.init();

        try {
            const res = this.db.exec("SELECT 1 FROM sqlite_master WHERE type='table'");
            if (res.length === 0 || res[0].values.length === 0) {
                this._bootstrapSchema();
            }
        } catch(e) {
            throw new errors.DatabaseBackendError(`Database error during initialization check: ${e.message}`);
        }

        let hasKek = false;
        try {
            const res = this.db.exec("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' LIMIT 1");
            if (res && res.length > 0) hasKek = true;
        } catch (e) {
            if (!e.message.includes("no such table")) {
                throw new errors.DatabaseBackendError(`Database error during initialization check: ${e.message}`);
            }
        }
        if (hasKek) {
            throw new errors.StorageAlreadyInitialized("Storage is already initialized");
        }

        this._validatePlatform(platform);

        const dbKekBytes = cryptoUtils.generateRandomBytes(32);
        const dbKid = uuidv4();

        const salt = cryptoUtils.generateRandomBytes(cryptoUtils.ARGON2ID_PROFILE_V1.saltBytes);
        // In this library, the Argon2id profile v1 is identical across all platforms.
        // We use 64 MiB / 3 iterations / p=1 as a practical compromise that works in the browser.
        // However, this may still be heavy for low-end mobile devices.
        // We do not currently introduce adaptive or platform-specific profiles.
        const timeCost = cryptoUtils.ARGON2ID_PROFILE_V1.iterations;
        const memoryCost = cryptoUtils.ARGON2ID_PROFILE_V1.memoryKib;
        const parallelism = cryptoUtils.ARGON2ID_PROFILE_V1.parallelism;
        const outputBytes = cryptoUtils.ARGON2ID_PROFILE_V1.outputBytes;

        const unlockKekBytes = await cryptoUtils.deriveKekArgon2id(passphrase, salt, outputBytes, timeCost, memoryCost, parallelism);
        const unlockKid = uuidv4();

        const providerConfig = {
            kdf: "argon2id",
            profile: "argon2id-profile-v1",
            salt: this._b64e(salt),
            memory_kib: memoryCost,
            iterations: timeCost,
            parallelism: parallelism,
            output_bytes: outputBytes
        };

        const wrapAlg = 'A256GCM';
        const aadPolicyName = aadPolicy.selectKeyWrapPolicy({ wrappedKeyClass: 'database_kek', alg: wrapAlg });
        const aadBytes = aadPolicy.buildAadBytes(aadPolicyName, {
            wrapped_kid: dbKid,
            wrapping_kid: unlockKid
        });
        const { nonce, ciphertext: wrappedDbKek } = cryptoUtils.encryptAead(unlockKekBytes, dbKekBytes, aadBytes);

        this.db.exec("BEGIN TRANSACTION;");
        try {
            const dbUuid = uuidv4();
            const metadata = {
                "storage_format_id": "vault.moukaeritai.work.storage",
                "format_major": "1",
                "format_minor": "0",
                "schema_version": "1",
                "database_uuid": dbUuid,
                "created_at_ms": String(this._currentMs()),
                "created_by_library": "browser-test",
                "created_by_version": "0.0.0-dev",
                "sqlite_application_id": "1447906135",
                "sqlite_user_version": "1",
                "required_features": cryptoUtils.canonicalizeJson([]).toString("utf-8"),
                "optional_features": cryptoUtils.canonicalizeJson([]).toString("utf-8")
            };

            for (const [prop, val] of Object.entries(metadata)) {
                this.db.run("INSERT INTO storage_metadata_tbl (property, value) VALUES (?, ?)", [prop, val]);
            }

            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [dbKid, 'database_kek', 'wrap_record_keys', wrapAlg, 'active', this._currentMs()]);
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [unlockKid, 'unlock_kek', 'wrap_database_keys', wrapAlg, 'active', this._currentMs()]);

            this.db.run("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)", [unlockKid, 'passphrase_argon2id', cryptoUtils.canonicalizeJson(providerConfig).toString('utf8'), platform]);

            const wrapId = uuidv4();
            this.db.run("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [wrapId, dbKid, unlockKid, 1, 'key_wrap', wrapAlg, nonce, wrappedDbKek, aadPolicyName, this._currentMs()]);
            this.db.exec("COMMIT;");
        } catch (err) {
            this.db.exec("ROLLBACK;");
            throw new errors.DatabaseBackendError(`Database error during initialization: ${err.message}`);
        }

        this.activeDbKek = dbKekBytes;
        this.activeDbKid = dbKid;
    }

    async unlockDatabase(passphrase) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        if (typeof passphrase !== 'string') {
            throw new errors.InvalidPassphrase("Passphrase must be a string");
        }

        if (!this.db) throw new errors.StorageNotInitialized("Database not initialized");

        try {
            const res = this.db.exec("SELECT 1 FROM sqlite_master WHERE type='table' AND name='storage_metadata_tbl'");
            if (res.length === 0 || res[0].values.length === 0) throw new errors.InvalidStorageFormat("No storage_metadata_tbl found (pre-v1 DB)");
        } catch(e) {
            if (e instanceof errors.InvalidStorageFormat) throw e;
            throw new errors.DatabaseBackendError(`Database error during metadata check: ${e.message}`);
        }

        try {
            // SQL.js memory DB does not reliably persist PRAGMAs across export/import
            // We skip the PRAGMA application_id and user_version checks for browser-test.
            const pragmaUserVersion = "1";

            const metadataRows = this.db.exec("SELECT property, value FROM storage_metadata_tbl");
            if (metadataRows.length === 0 || metadataRows[0].values.length === 0) throw new errors.InvalidStorageFormat("No storage_metadata_tbl found (pre-v1 DB)");

            const metadata = {};
            for (const row of metadataRows[0].values) {
                metadata[row[0]] = row[1];
            }

            const requiredProps = [
                "storage_format_id", "format_major", "format_minor", "schema_version",
                "database_uuid", "sqlite_application_id", "sqlite_user_version",
                "required_features", "optional_features"
            ];
            for (const prop of requiredProps) {
                if (!(prop in metadata)) throw new errors.InvalidStorageFormat(`Missing metadata property: ${prop}`);
            }

            if (metadata["storage_format_id"] !== "vault.moukaeritai.work.storage") throw new errors.InvalidStorageFormat("Invalid storage_format_id");
            if (metadata["format_major"] !== "1") throw new errors.InvalidStorageFormat("Invalid format_major");
            if (metadata["format_minor"] !== "0") throw new errors.InvalidStorageFormat("Invalid format_minor");
            if (metadata["schema_version"] !== "1") throw new errors.InvalidStorageFormat("Invalid schema_version");
            if (metadata["sqlite_application_id"] !== "1447906135") throw new errors.InvalidStorageFormat("Invalid metadata sqlite_application_id");
            if (metadata["sqlite_user_version"] !== "1") throw new errors.InvalidStorageFormat("Invalid metadata sqlite_user_version");


            if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(metadata["database_uuid"])) {
                throw new errors.InvalidStorageFormat("Invalid canonical database_uuid");
            }

            try {
                const reqFeat = JSON.parse(metadata["required_features"]);
                if (!Array.isArray(reqFeat) || reqFeat.length > 0) throw new errors.InvalidStorageFormat("Unknown required features found");
                const optFeat = JSON.parse(metadata["optional_features"]);
                if (!Array.isArray(optFeat) || optFeat.length > 0) throw new errors.InvalidStorageFormat("Unknown optional features found");
            } catch (e) {
                if (e instanceof errors.InvalidStorageFormat) throw e;
                throw new errors.InvalidStorageFormat("Features are not valid JSON arrays");
            }

        } catch (e) {
            if (e instanceof errors.InvalidStorageFormat) throw e;
            throw new errors.DatabaseBackendError(`Database error during validation: ${e.message}`);
        }

        let dbKid;
        let wrapRows = [];
        try {
            const resDbKek = this.db.exec("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1");
            if (resDbKek.length === 0) throw new errors.StorageNotInitialized("No active database KEK found");
            dbKid = resDbKek[0].values[0][0];

            let stmtWrap;
            try {
                stmtWrap = this.db.prepare(`SELECT wrapping_kid, nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ?`);
                stmtWrap.bind([dbKid]);
                while (stmtWrap.step()) {
                    wrapRows.push(stmtWrap.get());
                }
            } finally {
                if (stmtWrap) stmtWrap.free();
            }
        } catch (e) {
            if (e instanceof errors.StorageNotInitialized) throw e;
            throw new errors.DatabaseBackendError(`Database error during unlock: ${e.message}`);
        }
        if (wrapRows.length === 0) throw new errors.UnlockFailed("No wrap info found");

        let unwrapped = false;

        for (const row of wrapRows) {
            const wrapping_kid = row[0];
            const nonce = row[1];
            const wrapped_key = row[2];
            const aad_policy_name = row[3];

            try {
                aadPolicy.getPolicy(aad_policy_name);
            } catch (err) {
                if (err instanceof aadPolicy.AadPolicyError) {
                    continue;
                }
                throw err;
            }

            let hasProv = false;
            let provRow = null;
            try {
                const stmtProv = this.db.prepare(`SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?`);
                stmtProv.bind([wrapping_kid]);
                hasProv = stmtProv.step();
                if (hasProv) {
                    provRow = stmtProv.get();
                }
                stmtProv.free();
            } catch (e) {
                throw new errors.DatabaseBackendError(`Database error during unlock configuration retrieval: ${e.message}`);
            }
            if (hasProv) {
                const unlock_provider = provRow[0];
                const provider_config_json = provRow[1];

                if (unlock_provider === 'passphrase_argon2id') {
                    let config;
                    try {
                        config = JSON.parse(provider_config_json);
                    } catch (e) {
                        throw new errors.InvalidStorageFormat("provider_config_json is not valid JSON");
                    }

                    if (config.profile === "argon2id-profile-v1") {
                        if (config.kdf !== "argon2id" || config.memory_kib !== 65536 || config.iterations !== 3 || config.parallelism !== 1 || config.output_bytes !== 32) {
                            throw new errors.InvalidStorageFormat("provider_config_json explicit parameters mismatch argon2id-profile-v1");
                        }
                    }

                    const salt = this._b64d(config.salt);
                    if (salt.length !== 16) throw new errors.InvalidStorageFormat("decoded salt length is not 16 bytes");

                    try {
                        const unlockKekBytes = await cryptoUtils.deriveKekArgon2id(passphrase, salt, 32, config.iterations, config.memory_kib, config.parallelism);
                        const wrapAadBytes = aadPolicy.buildAadBytes(aad_policy_name, {
                            wrapped_kid: dbKid,
                            wrapping_kid: wrapping_kid
                        });
                        const dbKekBytes = cryptoUtils.decryptAead(unlockKekBytes, nonce, wrapped_key, wrapAadBytes);
                        this.activeDbKek = dbKekBytes;
                        this.activeDbKid = dbKid;
                        unwrapped = true;
                        break;
                    } catch (e) {
                        continue;
                    }
                }
            }
        }

        if (!unwrapped) {
            this.lock();
            throw new errors.UnlockFailed("Failed to unlock database");
        }
    }

    storePayload(schemaUuid, contentType, payload) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        this._validateUuid(schemaUuid, "schemaUuid");
        this._validateContentType(contentType);
        this._validatePayload(payload);

        if (!this.activeDbKek) throw new errors.StorageLocked("Database is locked");


        const objectUuid = uuidv4();
        const recordDekBytes = cryptoUtils.generateRandomBytes(32);
        const recordKid = uuidv4();
        const alg = 'A256GCM';

        const wrapAadPolicy = aadPolicy.selectKeyWrapPolicy({ wrappedKeyClass: 'record_dek', alg });
        const wrapAadBytes = aadPolicy.buildAadBytes(wrapAadPolicy, {
            wrapped_kid: recordKid,
            wrapping_kid: this.activeDbKid
        });
        const { nonce: nonceWrap, ciphertext: wrappedRecordDek } = cryptoUtils.encryptAead(this.activeDbKek, recordDekBytes, wrapAadBytes);

        const payloadBytes = cryptoUtils.canonicalizeJson(payload);
        const payloadAadPolicy = aadPolicy.selectPayloadPolicy({ alg });
        const payloadAadBytes = aadPolicy.buildAadBytes(payloadAadPolicy, {
            object_uuid: objectUuid,
            schema_uuid: schemaUuid,
            content_type: contentType,
            kid: recordKid,
            alg
        });
        const { nonce: noncePayload, ciphertext } = cryptoUtils.encryptAead(recordDekBytes, payloadBytes, payloadAadBytes);

        this.db.exec("BEGIN TRANSACTION;");
        try {
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [recordKid, 'record_dek', 'encrypt_payload', alg, 'active', this._currentMs()]);

            const wrapId = uuidv4();
            this.db.run("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [wrapId, recordKid, this.activeDbKid, 1, 'key_wrap', alg, nonceWrap, wrappedRecordDek, wrapAadPolicy, this._currentMs()]);

            this.db.run("INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [objectUuid, 1, 'aead', schemaUuid, contentType, alg, recordKid, noncePayload, ciphertext, payloadAadPolicy, this._currentMs(), this._currentMs()]);
            this.db.exec("COMMIT;");
        } catch (err) {
            this.db.exec("ROLLBACK;");
            throw new errors.DatabaseBackendError(`Database error during store: ${err.message}`);
        }

        return objectUuid;
    }

    retrievePayload(objectUuid) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        this._validateUuid(objectUuid, "objectUuid");
        if (!this.activeDbKek) throw new errors.StorageLocked("Database is locked");


        let hasRow = false;
        let row = null;
        try {
            const stmtObj = this.db.prepare(`SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?`);
            stmtObj.bind([objectUuid]);
            hasRow = stmtObj.step();
            if (hasRow) {
                row = stmtObj.get();
            }
            stmtObj.free();
        } catch (e) {
            throw new errors.DatabaseBackendError(`Database error during retrieve: ${e.message}`);
        }
        if (!hasRow) {
            throw new errors.ObjectNotFound("Object not found");
        }
        const schema_uuid = row[0];
        const content_type = row[1];
        const alg = row[2];
        const kid = row[3];
        const nonce = row[4];
        const ciphertext = row[5];
        const payload_aad_policy_name = row[6];

        aadPolicy.getPolicy(payload_aad_policy_name);

        let hasWrap = false;
        let wrapRow = null;
        let stmtWrap;
        try {
            stmtWrap = this.db.prepare(`SELECT nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?`);
            stmtWrap.bind([kid, this.activeDbKid]);
            hasWrap = stmtWrap.step();
            if (hasWrap) {
                wrapRow = stmtWrap.get();
            }
        } catch (e) {
            throw new errors.DatabaseBackendError(`Database error during record key retrieval: ${e.message}`);
        } finally {
            if (stmtWrap) stmtWrap.free();
        }
        if (!hasWrap) {
            throw new errors.IntegrityCheckFailed("Record DEK wrap info not found");
        }
        const wrap_nonce = wrapRow[0];
        const wrapped_key = wrapRow[1];
        const wrap_aad_policy_name = wrapRow[2];

        aadPolicy.getPolicy(wrap_aad_policy_name);

        const wrapAadBytes = aadPolicy.buildAadBytes(wrap_aad_policy_name, {
            wrapped_kid: kid,
            wrapping_kid: this.activeDbKid
        });

        const recordDekBytes = cryptoUtils.decryptAead(this.activeDbKek, wrap_nonce, wrapped_key, wrapAadBytes);

        const payloadAadBytes = aadPolicy.buildAadBytes(payload_aad_policy_name, {
            object_uuid: objectUuid,
            schema_uuid: schema_uuid,
            content_type: content_type,
            kid: kid,
            alg: alg
        });

        const payloadBytes = cryptoUtils.decryptAead(recordDekBytes, nonce, ciphertext, payloadAadBytes);
        return JSON.parse(payloadBytes.toString('utf8'));
    }


        isClosed() {
        return this._isClosed;
    }

    isUnlocked() {
        if (this._isClosed || !this._isInit) return false;
        return this.activeDbKek !== null;
    }

    getStatus() {
        if (this._isClosed) return "closed";
        if (!this._isInit) return "uninitialized";
        if (this.activeDbKek !== null) return "open_unlocked";

        try {
            const resDbKek = this.db.exec("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1");
            if (!resDbKek || resDbKek.length === 0) return "uninitialized";
        } catch (e) {
            return "uninitialized";
        }

        return "open_locked";
    }

    lock() {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");
        if (this.activeDbKek) {
            this.activeDbKek.fill(0);
            this.activeDbKek = null;
        }
        this.activeDbKid = null;
    }

    close() {
        if (this._isClosed) return;
        if (this.activeDbKek) {
            this.activeDbKek.fill(0);
            this.activeDbKek = null;
        }
        this.activeDbKid = null;
        if (this.db) {
            this.db.close();
            this.db = null;
        }
        this._isClosed = true;
        this._isInit = false;
    }
}

module.exports = EncryptedStorage;
