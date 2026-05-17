const fs = require('fs');

const storagePath = 'nodejs/src/storage.js';
let content = fs.readFileSync(storagePath, 'utf8');

const oldStore = `    storePayload(schemaUuid, contentType, payload) {
        if (!this.activeDbKek) throw new Error("Database is locked");

        const objectUuid = uuidv4();
        const recordDekBytes = cryptoUtils.generateRandomBytes(32);
        const recordKid = uuidv4();

        const insertKeyStmt = this.conn.prepare("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)");
        insertKeyStmt.run(recordKid, 'record_dek', 'encrypt_payload', 'A256GCM', 'active', this._currentMs());

        const wrapAad = {
            v: 1,
            aad_policy: "wrap-record-key-v1",
            wrapped_kid: recordKid,
            wrapping_kid: this.activeDbKid
        };
        const wrapAadBytes = cryptoUtils.canonicalizeJson(wrapAad);

        const { nonce: nonceWrap, ciphertext: wrappedRecordDek } = cryptoUtils.encryptAead(this.activeDbKek, recordDekBytes, wrapAadBytes);

        const insertWrappedKeyStmt = this.conn.prepare("INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)");
        insertWrappedKeyStmt.run(recordKid, this.activeDbKid, 'A256GCM', nonceWrap, wrappedRecordDek, wrapAadBytes.toString('utf8'), this._currentMs());

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

        const insertEncryptedObjectStmt = this.conn.prepare("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)");
        insertEncryptedObjectStmt.run(objectUuid, schemaUuid, contentType, 'A256GCM', recordKid, noncePayload, ciphertext, 'record-payload-v1', this._currentMs(), this._currentMs());

        return objectUuid;
    }`;

const newStore = `    storePayload(schemaUuid, contentType, payload) {
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
    }`;

content = content.replace(oldStore, newStore);
fs.writeFileSync(storagePath, content);
