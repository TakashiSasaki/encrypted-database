const initSqlJs = require('sql.js');
const { v4: uuidv4 } = require('uuid');
const cryptoUtils = require('./crypto');
const schemaSql = require('!!raw-loader!../../docs/schema.sql').default;

class EncryptedStorage {
    constructor() {
        this.db = null;
        this.activeDbKek = null;
        this.activeDbKid = null;
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

    async initializeDatabase(passphrase, platform = "web") {
        if (!this.db) await this.init();

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

        const aadContext = {
            v: 1,
            aad_policy: "wrap-database-key-v1",
            wrapped_kid: dbKid,
            wrapping_kid: unlockKid
        };
        const aadBytes = cryptoUtils.canonicalizeJson(aadContext);
        const { nonce, ciphertext: wrappedDbKek } = cryptoUtils.encryptAead(unlockKekBytes, dbKekBytes, aadBytes);

        this.db.exec("BEGIN TRANSACTION;");
        try {
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [dbKid, 'database_kek', 'wrap_record_keys', 'A256GCM', 'active', this._currentMs()]);
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [unlockKid, 'unlock_kek', 'wrap_database_keys', 'A256GCM', 'active', this._currentMs()]);

            this.db.run("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)", [unlockKid, 'passphrase_argon2id', JSON.stringify(providerConfig), platform]);

            this.db.run("INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)", [dbKid, unlockKid, 'A256GCM', nonce, wrappedDbKek, aadBytes.toString('utf8'), this._currentMs()]);
            this.db.exec("COMMIT;");
        } catch (err) {
            this.db.exec("ROLLBACK;");
            throw err;
        }

        this.activeDbKek = dbKekBytes;
        this.activeDbKid = dbKid;
    }

    async unlockDatabase(passphrase) {
        if (!this.db) throw new Error("Database not initialized");

        const resDbKek = this.db.exec("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1");
        if (resDbKek.length === 0) throw new Error("No active database KEK found");
        const dbKid = resDbKek[0].values[0][0];

        const resWrap = this.db.exec(`SELECT wrapping_kid, nonce, wrapped_key, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = '${dbKid}'`);
        if (resWrap.length === 0) throw new Error("No wrap info found");

        let unwrapped = false;

        for (const row of resWrap[0].values) {
            const wrapping_kid = row[0];
            const nonce = row[1];
            const wrapped_key = row[2];
            const aad_context_json = row[3];

            const resProv = this.db.exec(`SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = '${wrapping_kid}'`);
            if (resProv.length > 0) {
                const provRow = resProv[0].values[0];
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
            }
        }

        if (!unwrapped) throw new Error("Failed to unlock database");
    }

    storePayload(schemaUuid, contentType, payload) {
        if (!this.activeDbKek) throw new Error("Database is locked");

        const objectUuid = uuidv4();
        const recordDekBytes = cryptoUtils.generateRandomBytes(32);
        const recordKid = uuidv4();

        const wrapAad = {
            v: 1,
            aad_policy: "wrap-record-key-v1",
            wrapped_kid: recordKid,
            wrapping_kid: this.activeDbKid
        };
        const wrapAadBytes = cryptoUtils.canonicalizeJson(wrapAad);
        const { nonce: nonceWrap, ciphertext: wrappedRecordDek } = cryptoUtils.encryptAead(this.activeDbKek, recordDekBytes, wrapAadBytes);

        const payloadBytes = cryptoUtils.canonicalizeJson(payload);
        const payloadAad = {
            v: 1,
            aad_policy: "record-payload-v1",
            object_uuid: objectUuid,
            schema_uuid: schemaUuid,
            content_type: contentType,
            kid: recordKid,
            alg: "A256GCM"
        };
        const payloadAadBytes = cryptoUtils.canonicalizeJson(payloadAad);
        const { nonce: noncePayload, ciphertext } = cryptoUtils.encryptAead(recordDekBytes, payloadBytes, payloadAadBytes);

        this.db.exec("BEGIN TRANSACTION;");
        try {
            this.db.run("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", [recordKid, 'record_dek', 'encrypt_payload', 'A256GCM', 'active', this._currentMs()]);

            this.db.run("INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)", [recordKid, this.activeDbKid, 'A256GCM', nonceWrap, wrappedRecordDek, wrapAadBytes.toString('utf8'), this._currentMs()]);

            this.db.run("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [objectUuid, schemaUuid, contentType, 'A256GCM', recordKid, noncePayload, ciphertext, 'record-payload-v1', this._currentMs(), this._currentMs()]);
            this.db.exec("COMMIT;");
        } catch (err) {
            this.db.exec("ROLLBACK;");
            throw err;
        }

        return objectUuid;
    }

    retrievePayload(objectUuid) {
        if (!this.activeDbKek) throw new Error("Database is locked");

        let rowObj;
        const objStmt = this.db.prepare(
            'SELECT schema_uuid, content_type, kid, nonce, ciphertext FROM encrypted_object_tbl WHERE object_uuid = ?'
        );
        try {
            objStmt.bind([objectUuid]);
            if (!objStmt.step()) throw new Error("Object not found");
            rowObj = objStmt.getAsObject();
        } finally {
            objStmt.free();
        }
        const schema_uuid = rowObj.schema_uuid;
        const content_type = rowObj.content_type;
        const kid = rowObj.kid;
        const nonce = rowObj.nonce;
        const ciphertext = rowObj.ciphertext;

        let wrapRowObj;
        const wrapStmt = this.db.prepare(
            'SELECT nonce, wrapped_key, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?'
        );
        try {
            wrapStmt.bind([kid, this.activeDbKid]);
            if (!wrapStmt.step()) throw new Error("Record DEK wrap info not found");
            wrapRowObj = wrapStmt.getAsObject();
        } finally {
            wrapStmt.free();
        }
        const wrap_nonce = wrapRowObj.nonce;
        const wrapped_key = wrapRowObj.wrapped_key;
        const aad_context_json = wrapRowObj.aad_context_json;

        const recordDekBytes = cryptoUtils.decryptAead(this.activeDbKek, wrap_nonce, wrapped_key, Buffer.from(aad_context_json, 'utf8'));

        const payloadAad = {
            v: 1,
            aad_policy: "record-payload-v1",
            object_uuid: objectUuid,
            schema_uuid: schema_uuid,
            content_type: content_type,
            kid: kid,
            alg: "A256GCM"
        };
        const payloadAadBytes = cryptoUtils.canonicalizeJson(payloadAad);

        const payloadBytes = cryptoUtils.decryptAead(recordDekBytes, nonce, ciphertext, payloadAadBytes);
        return JSON.parse(payloadBytes.toString('utf8'));
    }


    lock() {
        if (this.activeDbKek) {
            this.activeDbKek.fill(0);
            this.activeDbKek = null;
        }
        this.activeDbKid = null;
    }

    close() {
        if (this.db) {
            this.db.close();
            this.db = null;
        }
        this.activeDbKek = null;
        this.activeDbKid = null;
    }
}

module.exports = EncryptedStorage;
