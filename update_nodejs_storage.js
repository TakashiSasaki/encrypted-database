const fs = require('fs');

const storagePath = 'nodejs/src/storage.js';
let content = fs.readFileSync(storagePath, 'utf8');

// Replace initializeDatabase
const oldInit = `    async initializeDatabase(passphrase, platform = "cross_platform") {
        const dbKekBytes = cryptoUtils.generateRandomBytes(32);
        const dbKid = uuidv4();

        const insertKeyStmt = this.conn.prepare("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)");
        insertKeyStmt.run(dbKid, 'database_kek', 'wrap_record_keys', 'A256GCM', 'active', this._currentMs());

        const salt = cryptoUtils.generateRandomBytes(16);
        const timeCost = 3;
        const memoryCost = 262144;
        const parallelism = 4;

        const unlockKekBytes = await cryptoUtils.deriveKekArgon2id(passphrase, salt, 32, timeCost, memoryCost, parallelism);
        const unlockKid = uuidv4();

        insertKeyStmt.run(unlockKid, 'unlock_kek', 'wrap_database_keys', 'A256GCM', 'active', this._currentMs());

        const providerConfig = {
            salt: this._b64e(salt),
            memory_kib: memoryCost,
            iterations: timeCost,
            parallelism: parallelism
        };

        const insertUnlockKekStmt = this.conn.prepare("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)");
        insertUnlockKekStmt.run(unlockKid, 'passphrase_argon2id', JSON.stringify(providerConfig), platform);

        const aadContext = {
            v: 1,
            aad_policy: "wrap-database-key-v1",
            wrapped_kid: dbKid,
            wrapping_kid: unlockKid
        };
        const aadBytes = cryptoUtils.canonicalizeJson(aadContext);

        const { nonce, ciphertext: wrappedDbKek } = cryptoUtils.encryptAead(unlockKekBytes, dbKekBytes, aadBytes);

        const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)");
        insertWrappedKeyStmt.run(dbKid, unlockKid, 'A256GCM', nonce, wrappedDbKek, aadBytes.toString('utf8'), this._currentMs());

        this.activeDbKek = dbKekBytes;
        this.activeDbKid = dbKid;
    }`;

const newInit = `    async initializeDatabase(passphrase, platform = "cross_platform") {
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
            insertUnlockKekStmt.run(unlockKid, 'passphrase_argon2id', JSON.stringify(providerConfig), platform);

            const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)");
            insertWrappedKeyStmt.run(dbKid, unlockKid, 'A256GCM', nonce, wrappedDbKek, aadBytes.toString('utf8'), this._currentMs());
        });
        runTransaction();

        this.activeDbKek = dbKekBytes;
        this.activeDbKid = dbKid;
    }`;

content = content.replace(oldInit, newInit);
fs.writeFileSync(storagePath, content);
