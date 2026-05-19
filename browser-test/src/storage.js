const initSqlJs = require('sql.js');
const { v4: uuidv4 } = require('uuid');
const aadPolicy = require('./aadPolicy');
const cryptoUtils = require('./crypto');
const errors = require('./errors');
const schemaSql = require('!!raw-loader!../../docs/backend/sqlite/schema.sql').default;

class EncryptedStorage {
    constructor() {
        this.db = null;
        this.activeDbKek = null;
        this.activeDbKid = null;
        this._isClosed = false;
        this._isInit = false;
    }

    async init() {
        // Init sql.js, pointing WASM locate to local file we copy via Webpack
        const SQL = await initSqlJs({
            locateFile: file => {
              if (file.endsWith('.wasm')) return 'sql-wasm.wasm';
              return file;
            }
        });
        this.db = new SQL.Database();
        this.db.exec("PRAGMA foreign_keys = ON;");
        this.db.exec(schemaSql);
        this._isClosed = false;
        this._isInit = true;
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
        const stmt = this.db.prepare('SELECT 1 FROM platform_tbl WHERE platform = ?');
        stmt.bind([platform]);
        const hasRow = stmt.step();
        stmt.free();
        if (!hasRow) {
            throw new errors.UnsupportedPlatform(`Unsupported platform: ${platform}`);
        }
    }

    async initializeDatabase(passphrase, platform = "web") {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");
        if (this.isUnlocked()) throw new errors.StorageAlreadyInitialized("Storage is already initialized");
        if (!this.db) await this.init();

        try {
            const hasKek = this.db.exec("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' LIMIT 1");
            if (hasKek && hasKek.length > 0) throw new errors.StorageAlreadyInitialized("Storage is already initialized");
        } catch (e) {
            if (e instanceof errors.StorageAlreadyInitialized) {
                throw e;
            }
            if (!e.message.includes("no such table")) {
                throw new errors.DatabaseBackendError(`Database error during initialization check: ${e.message}`);
            }
        }

        this._validatePlatform(platform);

        const dbKekBytes = cryptoUtils.generateRandomBytes(32);
        const dbKid = uuidv4();

        const salt = cryptoUtils.generateRandomBytes(16);
        // Using lower parameters for argon2 in browser context to avoid Out-Of-Memory
        // issues in typical test environments with argon2-browser.
        const timeCost = 2;
        const memoryCost = 16384;
        const parallelism = 1;

        const unlockKekBytes = await cryptoUtils.deriveKekArgon2id(passphrase, salt, 32, timeCost, memoryCost, parallelism);
        const unlockKid = uuidv4();

        const providerConfig = {
            salt: this._b64e(salt),
            memory_kib: memoryCost,
            iterations: timeCost,
            parallelism: parallelism
        };

        const wrapAlg = 'A256GCM';
        const aadPolicyName = aadPolicy.selectKeyWrapPolicy({ wrappedKeyClass: 'database_kek', alg: wrapAlg });
        const aadContext = aadPolicy.buildAadContext(aadPolicyName, {
            wrappedKid: dbKid,
            wrappingKid: unlockKid
        });
        const aadBytes = aadPolicy.buildAadBytes(aadPolicyName, {
            wrappedKid: dbKid,
            wrappingKid: unlockKid
        });
        const { nonce, ciphertext: wrappedDbKek } = cryptoUtils.encryptAead(unlockKekBytes, dbKekBytes, aadBytes);

        this.db.exec("BEGIN TRANSACTION;");
        try {
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [dbKid, 'database_kek', 'wrap_record_keys', wrapAlg, 'active', this._currentMs()]);
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [unlockKid, 'unlock_kek', 'wrap_database_keys', wrapAlg, 'active', this._currentMs()]);

            this.db.run("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)", [unlockKid, 'passphrase_argon2id', JSON.stringify(providerConfig), platform]);

            const wrapId = uuidv4();
            this.db.run("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [wrapId, dbKid, unlockKid, 1, 'key_wrap', wrapAlg, nonce, wrappedDbKek, aadPolicyName, cryptoUtils.canonicalizeJson(aadContext).toString('utf8'), this._currentMs()]);
            this.db.exec("COMMIT;");
        } catch (err) {
            this.db.exec("ROLLBACK;");
            throw err;
        }

        this.activeDbKek = dbKekBytes;
        this.activeDbKid = dbKid;
    }

    async unlockDatabase(passphrase) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");

        if (!this.db) throw new errors.StorageNotInitialized("Database not initialized");

        const resDbKek = this.db.exec("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1");
        if (resDbKek.length === 0) throw new errors.StorageNotInitialized("No active database KEK found");
        const dbKid = resDbKek[0].values[0][0];

        const stmtWrap = this.db.prepare(`SELECT wrapping_kid, nonce, wrapped_key, aad_policy, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ?`);
        stmtWrap.bind([dbKid]);
        const wrapRows = [];
        while (stmtWrap.step()) {
            wrapRows.push(stmtWrap.get());
        }
        stmtWrap.free();
        if (wrapRows.length === 0) throw new errors.UnlockFailed("No wrap info found");

        let unwrapped = false;

        for (const row of wrapRows) {
            const wrapping_kid = row[0];
            const nonce = row[1];
            const wrapped_key = row[2];
            const aad_policy_name = row[3];
            const aad_context_json = row[4];

            try {
                aadPolicy.getPolicy(aad_policy_name);
            } catch (err) {
                if (err instanceof aadPolicy.AadPolicyError) {
                    continue;
                }
                throw err;
            }

            const stmtProv = this.db.prepare(`SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?`);
            stmtProv.bind([wrapping_kid]);
            const hasProv = stmtProv.step();
            if (hasProv) {
                const provRow = stmtProv.get();
                stmtProv.free();
                const unlock_provider = provRow[0];
                const provider_config_json = provRow[1];

                if (unlock_provider === 'passphrase_argon2id') {
                    const config = JSON.parse(provider_config_json);
                    const salt = this._b64d(config.salt);
                    try {
                        const unlockKekBytes = await cryptoUtils.deriveKekArgon2id(passphrase, salt, 32, config.iterations, config.memory_kib, config.parallelism);
                        const dbKekBytes = cryptoUtils.decryptAead(unlockKekBytes, nonce, wrapped_key, Buffer.from(aad_context_json, 'utf8'));
                        this.activeDbKek = dbKekBytes;
                        this.activeDbKid = dbKid;
                        unwrapped = true;
                        break;
                    } catch (e) {
                        continue;
                    }
                }
            } else {
                stmtProv.free();
            }
        }

        if (!unwrapped) {
            this.lock();
            throw new errors.UnlockFailed("Failed to unlock database");
        }
    }

    storePayload(schemaUuid, contentType, payload) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");
        if (!this.activeDbKek) throw new errors.StorageLocked("Database is locked");


        const objectUuid = uuidv4();
        const recordDekBytes = cryptoUtils.generateRandomBytes(32);
        const recordKid = uuidv4();
        const alg = 'A256GCM';

        const wrapAadPolicy = aadPolicy.selectKeyWrapPolicy({ wrappedKeyClass: 'record_dek', alg });
        const wrapAad = aadPolicy.buildAadContext(wrapAadPolicy, {
            wrappedKid: recordKid,
            wrappingKid: this.activeDbKid
        });
        const wrapAadBytes = aadPolicy.buildAadBytes(wrapAadPolicy, {
            wrappedKid: recordKid,
            wrappingKid: this.activeDbKid
        });
        const { nonce: nonceWrap, ciphertext: wrappedRecordDek } = cryptoUtils.encryptAead(this.activeDbKek, recordDekBytes, wrapAadBytes);

        const payloadBytes = cryptoUtils.canonicalizeJson(payload);
        const payloadAadPolicy = aadPolicy.selectPayloadPolicy({ alg });
        const payloadAadBytes = aadPolicy.buildAadBytes(payloadAadPolicy, {
            objectUuid,
            schemaUuid,
            contentType,
            kid: recordKid,
            alg
        });
        const { nonce: noncePayload, ciphertext } = cryptoUtils.encryptAead(recordDekBytes, payloadBytes, payloadAadBytes);

        this.db.exec("BEGIN TRANSACTION;");
        try {
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [recordKid, 'record_dek', 'encrypt_payload', alg, 'active', this._currentMs()]);

            const wrapId = uuidv4();
            this.db.run("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [wrapId, recordKid, this.activeDbKid, 1, 'key_wrap', alg, nonceWrap, wrappedRecordDek, wrapAadPolicy, cryptoUtils.canonicalizeJson(wrapAad).toString('utf8'), this._currentMs()]);

            this.db.run("INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [objectUuid, 1, 'aead', schemaUuid, contentType, alg, recordKid, noncePayload, ciphertext, payloadAadPolicy, this._currentMs(), this._currentMs()]);
            this.db.exec("COMMIT;");
        } catch (err) {
            this.db.exec("ROLLBACK;");
            throw err;
        }

        return objectUuid;
    }

    retrievePayload(objectUuid) {
        if (this._isClosed) throw new errors.StorageClosed("Storage is closed");
        if (!this.activeDbKek) throw new errors.StorageLocked("Database is locked");


        const stmtObj = this.db.prepare(`SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?`);
        stmtObj.bind([objectUuid]);
        const hasObj = stmtObj.step();
        if (!hasObj) {
            stmtObj.free();
            throw new errors.ObjectNotFound("Object not found");
        }
        const row = stmtObj.get();
        stmtObj.free();
        const schema_uuid = row[0];
        const content_type = row[1];
        const alg = row[2];
        const kid = row[3];
        const nonce = row[4];
        const ciphertext = row[5];
        const payload_aad_policy_name = row[6];

        aadPolicy.getPolicy(payload_aad_policy_name);

        const stmtWrap = this.db.prepare(`SELECT nonce, wrapped_key, aad_policy, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?`);
        stmtWrap.bind([kid, this.activeDbKid]);
        const hasWrap = stmtWrap.step();
        if (!hasWrap) {
            stmtWrap.free();
            throw new errors.IntegrityCheckFailed("Record DEK wrap info not found");
        }
        const wrapRow = stmtWrap.get();
        stmtWrap.free();
        const wrap_nonce = wrapRow[0];
        const wrapped_key = wrapRow[1];
        const wrap_aad_policy_name = wrapRow[2];
        const aad_context_json = wrapRow[3];

        aadPolicy.getPolicy(wrap_aad_policy_name);

        const recordDekBytes = cryptoUtils.decryptAead(this.activeDbKek, wrap_nonce, wrapped_key, Buffer.from(aad_context_json, 'utf8'));

        const payloadAadBytes = aadPolicy.buildAadBytes(payload_aad_policy_name, {
            objectUuid,
            schemaUuid: schema_uuid,
            contentType: content_type,
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
