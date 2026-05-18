const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const cryptoUtils = require('./crypto');

class EncryptedStorage {
    constructor(dbPath) {
        this.dbPath = dbPath;
        this.conn = new Database(dbPath);
        this.conn.pragma('foreign_keys = ON');
        this._initDb();
        this.activeDbKek = null;
        this.activeDbKid = null;
    }

    _initDb() {
        const schemaPath = path.join(__dirname, '..', '..', 'docs', 'schema.sql');
        const schemaSql = fs.readFileSync(schemaPath, 'utf8');
        this.conn.exec(schemaSql);
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
            throw new Error('A concrete platform name is required; cross_platform is not allowed');
        }
        const row = this.conn.prepare('SELECT 1 FROM platform_tbl WHERE platform = ?').get(platform);
        if (!row) {
            throw new Error(`Unsupported platform: ${platform}`);
        }
    }

    async initializeDatabase(passphrase, platform) {
        this._validatePlatform(platform);

        const dbKekBytes = cryptoUtils.generateRandomBytes(32);
        const dbKid = uuidv4();

        const salt = cryptoUtils.generateRandomBytes(16);
        const timeCost = 3;
        const memoryCost = 262144;
        const parallelism = 4;

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

        const runTransaction = this.conn.transaction(() => {
            const insertKeyStmt = this.conn.prepare("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)");
            insertKeyStmt.run(dbKid, 'database_kek', 'wrap_record_keys', 'A256GCM', 'active', this._currentMs());
            insertKeyStmt.run(unlockKid, 'unlock_kek', 'wrap_database_keys', 'A256GCM', 'active', this._currentMs());

            const insertUnlockKekStmt = this.conn.prepare("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)");
            insertUnlockKekStmt.run(unlockKid, 'passphrase_argon2id', cryptoUtils.canonicalizeJson(providerConfig).toString('utf8'), platform);

            const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)");
            insertWrappedKeyStmt.run(dbKid, unlockKid, 'A256GCM', nonce, wrappedDbKek, aadBytes.toString('utf8'), this._currentMs());
        });
        runTransaction();

        this.activeDbKek = dbKekBytes;
        this.activeDbKid = dbKid;
    }

    async unlockDatabase(passphrase) {
        const findDbKekStmt = this.conn.prepare("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1");
        const row = findDbKekStmt.get();
        if (!row) throw new Error("No active database KEK found");
        const dbKid = row.kid;

        const findWrapStmt = this.conn.prepare("SELECT wrapping_kid, nonce, wrapped_key, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ?");
        const wrapRows = findWrapStmt.all(dbKid);

        let unwrapped = false;
        const findUnlockProviderStmt = this.conn.prepare("SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?");

        for (const wrapRow of wrapRows) {
            const provRow = findUnlockProviderStmt.get(wrapRow.wrapping_kid);
            if (provRow && provRow.unlock_provider === 'passphrase_argon2id') {
                const config = JSON.parse(provRow.provider_config_json);
                const salt = this._b64d(config.salt);
                try {
                    const unlockKekBytes = await cryptoUtils.deriveKekArgon2id(passphrase, salt, 32, config.iterations, config.memory_kib, config.parallelism);
                    const dbKekBytes = cryptoUtils.decryptAead(unlockKekBytes, wrapRow.nonce, wrapRow.wrapped_key, Buffer.from(wrapRow.aad_context_json, 'utf8'));
                    this.activeDbKek = dbKekBytes;
                    this.activeDbKid = dbKid;
                    unwrapped = true;
                    break;
                } catch (e) {
                    continue;
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

        const runTransaction = this.conn.transaction(() => {
            const insertKeyStmt = this.conn.prepare("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)");
            insertKeyStmt.run(recordKid, 'record_dek', 'encrypt_payload', 'A256GCM', 'active', this._currentMs());

            const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)");
            insertWrappedKeyStmt.run(recordKid, this.activeDbKid, 'A256GCM', nonceWrap, wrappedRecordDek, wrapAadBytes.toString('utf8'), this._currentMs());

            const insertEncryptedObjectStmt = this.conn.prepare("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
            insertEncryptedObjectStmt.run(objectUuid, schemaUuid, contentType, 'A256GCM', recordKid, noncePayload, ciphertext, 'record-payload-v1', this._currentMs(), this._currentMs());
        });
        runTransaction();

        return objectUuid;
    }

    retrievePayload(objectUuid) {
        if (!this.activeDbKek) throw new Error("Database is locked");

        const findObjectStmt = this.conn.prepare("SELECT schema_uuid, content_type, kid, nonce, ciphertext FROM encrypted_object_tbl WHERE object_uuid = ?");
        const row = findObjectStmt.get(objectUuid);
        if (!row) throw new Error("Object not found");

        const findWrapStmt = this.conn.prepare("SELECT nonce, wrapped_key, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?");
        const wrapRow = findWrapStmt.get(row.kid, this.activeDbKid);
        if (!wrapRow) throw new Error("Record DEK wrap info not found");

        const recordDekBytes = cryptoUtils.decryptAead(this.activeDbKek, wrapRow.nonce, wrapRow.wrapped_key, Buffer.from(wrapRow.aad_context_json, 'utf8'));

        const payloadAad = {
            v: 1,
            aad_policy: "record-payload-v1",
            object_uuid: objectUuid,
            schema_uuid: row.schema_uuid,
            content_type: row.content_type,
            kid: row.kid,
            alg: "A256GCM"
        };
        const payloadAadBytes = cryptoUtils.canonicalizeJson(payloadAad);

        const payloadBytes = cryptoUtils.decryptAead(recordDekBytes, row.nonce, row.ciphertext, payloadAadBytes);
        return JSON.parse(payloadBytes.toString('utf8'));
    }

    close() {
        this.conn.close();
        this.activeDbKek = null;
        this.activeDbKid = null;
    }
}

module.exports = EncryptedStorage;
