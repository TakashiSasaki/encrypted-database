const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const aadPolicy = require('./aadPolicy');
const cryptoUtils = require('./crypto');
const errors = require('./errors');

class EncryptedStorage {
    static _UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;

    constructor(dbPath) {
        this.dbPath = dbPath;
        this.conn = new Database(dbPath);
        this.conn.pragma('foreign_keys = ON');


        this.activeDbKek = null;
        this.activeDbKid = null;
        this._isClosed = false;
    }

    _bootstrapSchema() {
        const schemaPath = path.join(__dirname, '..', '..', 'docs', 'backend', 'sqlite', 'schema.sql');
        const schemaSql = fs.readFileSync(schemaPath, 'utf8');
        this.conn.exec("PRAGMA application_id = 1447906135; PRAGMA user_version = 1; " + schemaSql);
    }

    _currentMs() {
        return Date.now();
    }

    _b64e(b) {
        return b.toString('base64url');
    }

    _b64d(s) {
        return Buffer.from(s, 'base64url');
    }

    _validatePlatform(platform) {
        if (!platform || platform === 'cross_platform') {
            throw new errors.UnsupportedPlatform('A concrete platform name is required; cross_platform is not allowed');
        }
        let row;
        try {
            row = this.conn.prepare('SELECT 1 FROM platform_tbl WHERE platform = ?').get(platform);
        } catch (e) {
            if (e.message.includes("no such table")) {
                throw new errors.UnsupportedPlatform(`Unsupported platform: ${platform}`);
            }
            throw new errors.DatabaseBackendError(`Database error during platform validation: ${e.message}`);
        }
        if (!row) {
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
        // Check for control characters
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

    _validateV1Metadata() {
        try {
            const row = this.conn.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='storage_metadata_tbl'").get();
            if (!row) throw new errors.InvalidStorageFormat("No storage_metadata_tbl found (pre-v1 DB)");
        } catch(e) {
            if (e instanceof errors.InvalidStorageFormat) throw e;
            throw new errors.DatabaseBackendError(`Database error during metadata check: ${e.message}`);
        }

        try {
            const pragmaAppId = this.conn.pragma("application_id", { simple: true });
            if (String(pragmaAppId) !== "1447906135") {
                throw new errors.InvalidStorageFormat(`Invalid PRAGMA application_id: ${pragmaAppId}`);
            }

            const pragmaUserVersion = this.conn.pragma("user_version", { simple: true });

            const metadataRows = this.conn.prepare("SELECT property, value FROM storage_metadata_tbl").all();
            if (metadataRows.length === 0) throw new errors.InvalidStorageFormat("storage_metadata_tbl is empty (invalid V1 DB)");

            const metadata = {};
            for (const row of metadataRows) {
                metadata[row.property] = row.value;
            }

            const requiredProps = [
                "storage_format_id", "format_major", "format_minor", "schema_version",
                "database_uuid", "created_at_ms", "created_by_library", "created_by_version",
                "sqlite_application_id", "sqlite_user_version",
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
            if (String(pragmaUserVersion) !== "1") throw new errors.InvalidStorageFormat("PRAGMA user_version and metadata contradiction");

            if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(metadata["database_uuid"])) {
                throw new errors.InvalidStorageFormat("Invalid canonical database_uuid");
            }

            if (!/^[0-9]+$/.test(metadata["created_at_ms"])) throw new errors.InvalidStorageFormat("Invalid created_at_ms format");
            if (typeof metadata["created_by_library"] !== 'string' || metadata["created_by_library"].trim() === '') throw new errors.InvalidStorageFormat("Invalid created_by_library");
            if (typeof metadata["created_by_version"] !== 'string' || metadata["created_by_version"].trim() === '') throw new errors.InvalidStorageFormat("Invalid created_by_version");

            try {
                const reqFeatStr = metadata["required_features"];
                const reqFeat = JSON.parse(reqFeatStr);
                if (cryptoUtils.canonicalizeJson(reqFeat).toString('utf-8') !== reqFeatStr) {
                    throw new errors.InvalidStorageFormat("Features are not valid JCS canonical JSON arrays");
                }
                if (!Array.isArray(reqFeat) || reqFeat.length > 0) throw new errors.InvalidStorageFormat("Unknown required features found");

                const optFeatStr = metadata["optional_features"];
                const optFeat = JSON.parse(optFeatStr);
                if (cryptoUtils.canonicalizeJson(optFeat).toString('utf-8') !== optFeatStr) {
                    throw new errors.InvalidStorageFormat("Features are not valid JCS canonical JSON arrays");
                }
                if (!Array.isArray(optFeat) || optFeat.length > 0) throw new errors.InvalidStorageFormat("Unknown optional features found");
            } catch (e) {
                if (e instanceof errors.InvalidStorageFormat) throw e;
                throw new errors.InvalidStorageFormat("Features are not valid JSON arrays");
            }

        } catch (e) {
            if (e instanceof errors.InvalidStorageFormat) throw e;
            throw new errors.DatabaseBackendError(`Database error during validation: ${e.message}`);
        }
    }

    async initializeDatabase(passphrase, platform) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        if (typeof passphrase !== 'string') {
            throw new errors.InvalidPassphrase("Passphrase must be a string");
        }
        if (typeof platform !== 'string') {
            throw new errors.UnsupportedPlatform("Platform must be a string");
        }

        if (this.isUnlocked()) throw new errors.StorageAlreadyInitialized("Storage is already initialized");
        let hasKek = false;
        try {
            const row = this.conn.prepare("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' LIMIT 1").get();
            if (row) hasKek = true;
        } catch (e) {
            if (!e.message.includes("no such table")) {
                throw new errors.DatabaseBackendError(`Database error during initialization check: ${e.message}`);
            }
        }
        if (hasKek) {
            throw new errors.StorageAlreadyInitialized("Storage is already initialized");
        }

        try {
            const res = this.conn.prepare("SELECT 1 FROM sqlite_master WHERE type='table'").get();
            if (!res) {
                this._bootstrapSchema();
            } else {
                const hasMeta = this.conn.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='storage_metadata_tbl'").get();
                if (!hasMeta) throw new errors.InvalidStorageFormat("Cannot initialize non-empty pre-v1 database");
                const hasKeyTbl = this.conn.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name='key_tbl'").get();
                if (!hasKeyTbl) throw new errors.InvalidStorageFormat("Cannot initialize unsupported database format");
            }
        } catch(e) {
            if (e instanceof errors.InvalidStorageFormat) throw e;
            throw new errors.DatabaseBackendError(`Database error during initialization check: ${e.message}`);
        }

        this._validatePlatform(platform);

        const dbKekBytes = cryptoUtils.generateRandomBytes(32);
        const dbKid = uuidv4();

        const salt = cryptoUtils.generateRandomBytes(cryptoUtils.ARGON2ID_PROFILE_V1.saltBytes);
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

        // Wrap database KEK with unlock KEK. The library selects the AAD policy
        // from the operation and wrapped key class; callers do not provide it.
        const wrapAlg = 'A256GCM';
        const aadPolicyName = aadPolicy.selectKeyWrapPolicy({ wrappedKeyClass: 'database_kek', alg: wrapAlg });
        const aadContext = aadPolicy.buildAadContext(aadPolicyName, {
            wrapped_kid: dbKid,
            wrapping_kid: unlockKid
        });
        const aadBytes = aadPolicy.buildAadBytes(aadPolicyName, {
            wrapped_kid: dbKid,
            wrapping_kid: unlockKid
        });
        const { nonce, ciphertext: wrappedDbKek } = cryptoUtils.encryptAead(unlockKekBytes, dbKekBytes, aadBytes);

        const runTransaction = this.conn.transaction(() => {
            const dbUuid = uuidv4();

            const metadata = {
                "storage_format_id": "vault.moukaeritai.work.storage",
                "format_major": "1",
                "format_minor": "0",
                "schema_version": "1",
                "database_uuid": dbUuid,
                "created_at_ms": String(this._currentMs()),
                "created_by_library": "nodejs",
                "created_by_version": "0.0.0-dev",
                "sqlite_application_id": "1447906135",
                "sqlite_user_version": "1",
                "required_features": cryptoUtils.canonicalizeJson([]).toString("utf-8"),
                "optional_features": cryptoUtils.canonicalizeJson([]).toString("utf-8")
            };
            const insertMetadataStmt = this.conn.prepare("INSERT INTO storage_metadata_tbl (property, value) VALUES (?, ?)");
            for (const [prop, val] of Object.entries(metadata)) {
                insertMetadataStmt.run(prop, val);
            }

            const insertKeyStmt = this.conn.prepare("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)");
            insertKeyStmt.run(dbKid, 'database_kek', 'wrap_record_keys', wrapAlg, 'active', this._currentMs());
            insertKeyStmt.run(unlockKid, 'unlock_kek', 'wrap_database_keys', wrapAlg, 'active', this._currentMs());

            const insertUnlockKekStmt = this.conn.prepare("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)");
            insertUnlockKekStmt.run(unlockKid, 'passphrase_argon2id', cryptoUtils.canonicalizeJson(providerConfig).toString('utf8'), platform);

            const wrapId = uuidv4();
            const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
            insertWrappedKeyStmt.run(wrapId, dbKid, unlockKid, 1, 'key_wrap', wrapAlg, nonce, wrappedDbKek, aadPolicyName, this._currentMs());
        });

        try {
            runTransaction();
            this.conn.pragma("application_id = 1447906135");
            this.conn.pragma("user_version = 1");
        } catch (e) {
            throw new errors.DatabaseBackendError(`Database error during initialization: ${e.message}`);
        }

        this.activeDbKek = dbKekBytes;
        this.activeDbKid = dbKid;
    }

    async unlockDatabase(passphrase) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        if (typeof passphrase !== 'string') {
            throw new errors.InvalidPassphrase("Passphrase must be a string");
        }

        this._validateV1Metadata();

        let dbKid;
        let wrapRows;
        let findUnlockProviderStmt;
        try {
            const findDbKekStmt = this.conn.prepare("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1");
            const row = findDbKekStmt.get();
            if (!row) throw new errors.StorageNotInitialized("No active database KEK found");
            dbKid = row.kid;

            const findWrapStmt = this.conn.prepare("SELECT wrapping_kid, nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ?");
            wrapRows = findWrapStmt.all(dbKid);
            findUnlockProviderStmt = this.conn.prepare("SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?");
        } catch (e) {
            if (e instanceof errors.StorageNotInitialized) throw e;
            throw new errors.DatabaseBackendError(`Database error during unlock: ${e.message}`);
        }

        let unwrapped = false;

        for (const wrapRow of wrapRows) {
            try {
                aadPolicy.getPolicy(wrapRow.aad_policy);
            } catch (err) {
                if (err instanceof aadPolicy.AadPolicyError) {
                    continue;
                }
                throw err;
            }

            let provRow;
            try {
                provRow = findUnlockProviderStmt.get(wrapRow.wrapping_kid);
            } catch (e) {
                throw new errors.DatabaseBackendError(`Database error during unlock configuration retrieval: ${e.message}`);
            }
            if (provRow && provRow.unlock_provider === 'passphrase_argon2id') {
                const provConfigStr = provRow.provider_config_json;
                let config;
                try {
                    config = JSON.parse(provConfigStr);
                    const canonicalConfig = cryptoUtils.canonicalizeJson(config).toString('utf-8');
                    if (canonicalConfig !== provConfigStr) {
                        throw new errors.InvalidStorageFormat("provider_config_json is not valid JCS canonical JSON");
                    }
                } catch (e) {
                    if (e instanceof errors.InvalidStorageFormat) throw e;
                    throw new errors.InvalidStorageFormat("provider_config_json is not valid JSON");
                }

                const requiredConfigProps = ["kdf", "profile", "salt", "memory_kib", "iterations", "parallelism", "output_bytes"];
                for (const prop of requiredConfigProps) {
                    if (!(prop in config)) {
                        throw new errors.InvalidStorageFormat(`Missing provider_config_json property: ${prop}`);
                    }
                }

                if (config.profile !== "argon2id-profile-v1") {
                    throw new errors.InvalidStorageFormat("Unknown or missing profile in provider_config_json");
                }

                if (config.kdf !== "argon2id" || config.memory_kib !== 65536 || config.iterations !== 3 || config.parallelism !== 1 || config.output_bytes !== 32) {
                    throw new errors.InvalidStorageFormat("provider_config_json explicit parameters mismatch argon2id-profile-v1");
                }

                const saltStr = config.salt;
                if (saltStr.includes('=') || !/^[A-Za-z0-9_-]+$/.test(saltStr)) {
                    throw new errors.InvalidStorageFormat("salt must be base64url encoded with no padding");
                }

                let salt;
                try {
                    salt = this._b64d(saltStr);
                } catch (e) {
                    throw new errors.InvalidStorageFormat("salt is not valid base64url");
                }

                if (salt.length !== 16) throw new errors.InvalidStorageFormat("decoded salt length is not 16 bytes");

                try {
                    const unlockKekBytes = await cryptoUtils.deriveKekArgon2id(passphrase, salt, 32, config.iterations, config.memory_kib, config.parallelism);
                    const wrapAadBytes = aadPolicy.buildAadBytes(wrapRow.aad_policy, {
                        wrapped_kid: dbKid,
                        wrapping_kid: wrapRow.wrapping_kid
                    });
                    const dbKekBytes = cryptoUtils.decryptAead(unlockKekBytes, wrapRow.nonce, wrapRow.wrapped_key, wrapAadBytes);
                    this.activeDbKek = dbKekBytes;
                    this.activeDbKid = dbKid;
                    unwrapped = true;
                    break;
                } catch (e) {
                    continue;
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
        const wrapAad = aadPolicy.buildAadContext(wrapAadPolicy, {
            wrapped_kid: recordKid,
            wrapping_kid: this.activeDbKid
        });
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

        const runTransaction = this.conn.transaction(() => {
            const insertKeyStmt = this.conn.prepare("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)");
            insertKeyStmt.run(recordKid, 'record_dek', 'encrypt_payload', alg, 'active', this._currentMs());

            const wrapId = uuidv4();
            const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
            insertWrappedKeyStmt.run(wrapId, recordKid, this.activeDbKid, 1, 'key_wrap', alg, nonceWrap, wrappedRecordDek, wrapAadPolicy, this._currentMs());

            const insertEncryptedObjectStmt = this.conn.prepare("INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
            insertEncryptedObjectStmt.run(objectUuid, 1, 'aead', schemaUuid, contentType, alg, recordKid, noncePayload, ciphertext, payloadAadPolicy, this._currentMs(), this._currentMs());
        });

        try {
            runTransaction();
        } catch (e) {
            throw new errors.DatabaseBackendError(`Database error during store: ${e.message}`);
        }

        return objectUuid;
    }

    retrievePayload(objectUuid) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        this._validateUuid(objectUuid, "objectUuid");
        if (!this.activeDbKek) throw new errors.StorageLocked("Database is locked");


        let row;
        try {
            const findObjectStmt = this.conn.prepare("SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?");
            row = findObjectStmt.get(objectUuid);
        } catch (e) {
            throw new errors.DatabaseBackendError(`Database error during retrieve: ${e.message}`);
        }
        if (!row) throw new errors.ObjectNotFound("Object not found");

        aadPolicy.getPolicy(row.aad_policy);

        let wrapRow;
        try {
            const findWrapStmt = this.conn.prepare("SELECT nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?");
            wrapRow = findWrapStmt.get(row.kid, this.activeDbKid);
        } catch (e) {
            throw new errors.DatabaseBackendError(`Database error during record key retrieval: ${e.message}`);
        }
        if (!wrapRow) throw new errors.IntegrityCheckFailed("Record DEK wrap info not found");
        aadPolicy.getPolicy(wrapRow.aad_policy);

        const wrapAadBytes = aadPolicy.buildAadBytes(wrapRow.aad_policy, {
            wrapped_kid: row.kid,
            wrapping_kid: this.activeDbKid
        });

        const recordDekBytes = cryptoUtils.decryptAead(this.activeDbKek, wrapRow.nonce, wrapRow.wrapped_key, wrapAadBytes);

        const payloadAadBytes = aadPolicy.buildAadBytes(row.aad_policy, {
            object_uuid: objectUuid,
            schema_uuid: row.schema_uuid,
            content_type: row.content_type,
            kid: row.kid,
            alg: row.alg
        });

        const payloadBytes = cryptoUtils.decryptAead(recordDekBytes, row.nonce, row.ciphertext, payloadAadBytes);
        return JSON.parse(payloadBytes.toString('utf8'));
    }

    isClosed() {
        return this._isClosed;
    }

    isUnlocked() {
        if (this._isClosed) return false;
        return this.activeDbKek !== null;
    }

    getStatus() {
        if (this._isClosed) return "closed";
        if (this.activeDbKek !== null) return "open_unlocked";

        try {
            const resDbKek = this.conn.prepare("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1").get();
            if (!resDbKek) return "uninitialized";
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
        if (this.conn) {
            this.conn.close();
            this.conn = null;
        }
        this._isClosed = true;
    }
}

module.exports = EncryptedStorage;
