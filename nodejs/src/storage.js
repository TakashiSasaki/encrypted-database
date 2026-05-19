const Database = require('better-sqlite3');
const fs = require('fs');
const path = require('path');
const { v4: uuidv4 } = require('uuid');
const aadPolicy = require('./aadPolicy');
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
        const schemaPath = path.join(__dirname, '..', '..', 'docs', 'backend', 'sqlite', 'schema.sql');
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
            const insertKeyStmt = this.conn.prepare("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)");
            insertKeyStmt.run(dbKid, 'database_kek', 'wrap_record_keys', wrapAlg, 'active', this._currentMs());
            insertKeyStmt.run(unlockKid, 'unlock_kek', 'wrap_database_keys', wrapAlg, 'active', this._currentMs());

            const insertUnlockKekStmt = this.conn.prepare("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)");
            insertUnlockKekStmt.run(unlockKid, 'passphrase_argon2id', cryptoUtils.canonicalizeJson(providerConfig).toString('utf8'), platform);

            const wrapId = uuidv4();
            const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
            insertWrappedKeyStmt.run(wrapId, dbKid, unlockKid, 1, 'key_wrap', wrapAlg, nonce, wrappedDbKek, aadPolicyName, this._currentMs());
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

        const findWrapStmt = this.conn.prepare("SELECT wrapping_kid, nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ?");
        const wrapRows = findWrapStmt.all(dbKid);

        let unwrapped = false;
        const findUnlockProviderStmt = this.conn.prepare("SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?");

        for (const wrapRow of wrapRows) {
            try {
                aadPolicy.getPolicy(wrapRow.aad_policy);
            } catch (err) {
                if (err instanceof aadPolicy.AadPolicyError) {
                    continue;
                }
                throw err;
            }

            const provRow = findUnlockProviderStmt.get(wrapRow.wrapping_kid);
            if (provRow && provRow.unlock_provider === 'passphrase_argon2id') {
                const config = JSON.parse(provRow.provider_config_json);
                const salt = this._b64d(config.salt);
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

        if (!unwrapped) throw new Error("Failed to unlock database");
    }

    storePayload(schemaUuid, contentType, payload) {
        if (!this.activeDbKek) throw new Error("Database is locked");

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
        runTransaction();

        return objectUuid;
    }

    retrievePayload(objectUuid) {
        if (!this.activeDbKek) throw new Error("Database is locked");

        const findObjectStmt = this.conn.prepare("SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?");
        const row = findObjectStmt.get(objectUuid);
        if (!row) throw new Error("Object not found");

        aadPolicy.getPolicy(row.aad_policy);

        const findWrapStmt = this.conn.prepare("SELECT nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?");
        const wrapRow = findWrapStmt.get(row.kid, this.activeDbKid);
        if (!wrapRow) throw new Error("Record DEK wrap info not found");
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

    close() {
        this.conn.close();
        this.activeDbKek = null;
        this.activeDbKid = null;
    }
}

module.exports = EncryptedStorage;
