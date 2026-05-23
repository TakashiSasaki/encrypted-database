const fs = require('fs');
const path = require('path');
const os = require('os');
const Database = require('better-sqlite3');
const EncryptedStorage = require('../src/storage');
const errors = require('../src/errors');

describe('SQL Constraints V1', () => {
    let dbPath;

    beforeEach(() => {
        const tempDir = fs.mkdtempSync(path.join(os.tmpdir(), 'constraint-test-'));
        dbPath = path.join(tempDir, 'test.db');
    });

    afterEach(() => {
        if (fs.existsSync(dbPath)) {
            fs.unlinkSync(dbPath);
        }
        const tempDir = path.dirname(dbPath);
        if (fs.existsSync(tempDir)) {
            fs.rmdirSync(tempDir);
        }
    });

    it('should enforce CHECK constraints on database', async () => {
        const storage = new EncryptedStorage(dbPath);
        await storage.initializeDatabase("password", "linux");

        const db = new Database(dbPath);
        db.pragma('foreign_keys = ON');

        const row = db.prepare("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' LIMIT 1").get();
        const dbKid = row.kid;

        const objectUuid = "12345678-1234-4234-8234-123456789012";

        // 1. encrypted_object_tbl.nonce 12 bytes
        expect(() => {
            db.prepare("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)").run(
                objectUuid, objectUuid, 1, "aead", "application/json", "A256GCM", dbKid, Buffer.alloc(10), Buffer.alloc(16), "none"
            );
        }).toThrow();

        // 2. encrypted_object_tbl.ciphertext >= 16 bytes
        expect(() => {
            db.prepare("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)").run(
                objectUuid, objectUuid, 1, "aead", "application/json", "A256GCM", dbKid, Buffer.alloc(12), Buffer.alloc(10), "none"
            );
        }).toThrow();

        // 3. encrypted_object_tbl.content_type empty string
        expect(() => {
            db.prepare("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)").run(
                objectUuid, objectUuid, 1, "aead", "", "A256GCM", dbKid, Buffer.alloc(12), Buffer.alloc(16), "none"
            );
        }).toThrow();

        // 4. encrypted_object_tbl.content_type no slash
        expect(() => {
            db.prepare("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)").run(
                objectUuid, objectUuid, 1, "aead", "noslash", "A256GCM", dbKid, Buffer.alloc(12), Buffer.alloc(16), "none"
            );
        }).toThrow();

        // 5. wrapped_key_tbl.nonce 12 bytes
        const wrapId = "00000000-0000-4000-8000-000000000000";
        expect(() => {
            db.prepare("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)").run(
                wrapId, dbKid, dbKid, 1, "key_wrap", "A256GCM", Buffer.alloc(10), Buffer.alloc(32), "policy", 123
            );
        }).toThrow();

        // 6. wrapped_key_tbl.wrapped_key >= 16 bytes
        expect(() => {
            db.prepare("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)").run(
                wrapId, dbKid, dbKid, 1, "key_wrap", "A256GCM", Buffer.alloc(12), Buffer.alloc(10), "policy", 123
            );
        }).toThrow();

        db.close();
        storage.close();
    });
});
