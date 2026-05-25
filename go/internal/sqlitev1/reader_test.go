package sqlitev1

import (
	"crypto/aes"
	"crypto/cipher"
	"database/sql"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/aad"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"golang.org/x/crypto/argon2"
	_ "modernc.org/sqlite"
)

// This fixture is a deterministic minimal reader fixture, not a writer implementation.
func createTestDB(t *testing.T, dbPath, passphrase string) (string, string) {
	// Read schema
	schemaBytes, err := os.ReadFile("../../../docs/backend/sqlite/schema.sql")
	if err != nil {
		t.Fatalf("failed to read schema: %v", err)
	}

	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		t.Fatalf("failed to open test db: %v", err)
	}
	defer db.Close()

	// Apply schema
	_, err = db.Exec(string(schemaBytes))
	if err != nil {
		t.Fatalf("failed to apply schema: %v", err)
	}

	// PRAGMAs
	db.Exec("PRAGMA application_id = 1447906135")
	db.Exec("PRAGMA user_version = 1")

	nowMs := time.Now().UnixMilli()

	// Metadata
	metadata := []struct{ p, v string }{
		{"storage_format_id", "vault.moukaeritai.work.storage"},
		{"format_major", "1"},
		{"format_minor", "0"},
		{"schema_version", "1"},
		{"database_uuid", "11111111-1111-4111-8111-111111111111"},
		{"created_at_ms", fmt.Sprintf("%d", nowMs)},
		{"created_by_library", "go-test"},
		{"created_by_version", "1.0"},
		{"sqlite_application_id", "1447906135"},
		{"sqlite_user_version", "1"},
		{"required_features", "[]"},
		{"optional_features", "[]"},
	}

	for _, m := range metadata {
		_, err := db.Exec("INSERT INTO storage_metadata_tbl (property, value) VALUES (?, ?)", m.p, m.v)
		if err != nil {
			t.Fatalf("failed to insert metadata: %v", err)
		}
	}

	// Deterministic keys and nonces for testing only
	dbKid := "22222222-2222-4222-8222-222222222222"
	unlockKid := "33333333-3333-4333-8333-333333333333"
	recordKid := "44444444-4444-4444-8444-444444444444"
	objectUuid := "55555555-5555-4555-8555-555555555555"
	schemaUuid := "66666666-6666-4666-8666-666666666666"

	dbKek := bytesOf(32, 0x11)
	recordDek := bytesOf(32, 0x22)

	// Key Tbl
	insertKey(t, db, dbKid, "database_kek", "wrap_record_keys", "A256GCM", "active", nowMs)
	insertKey(t, db, unlockKid, "unlock_kek", "wrap_database_keys", "A256GCM", "active", nowMs)
	insertKey(t, db, recordKid, "record_dek", "encrypt_payload", "A256GCM", "active", nowMs)

	// Unlock KEK
	config := map[string]interface{}{
		"kdf":          "argon2id",
		"profile":      "argon2id-profile-v1",
		"salt":         "QUJDREVGR0hJSktMTU5PUA", // base64url of "ABCDEFGHIJKLMNOP"
		"memory_kib":   65536,
		"iterations":   3,
		"parallelism":  1,
		"output_bytes": 32,
	}
	configJcs, _ := jcs.Canonicalize(config)
	_, err = db.Exec("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)",
		unlockKid, "passphrase_argon2id", configJcs, "server")
	if err != nil {
		t.Fatalf("failed to insert unlock kek: %v", err)
	}

	// Derive unlock KEK
	salt := []byte("ABCDEFGHIJKLMNOP")
	unlockKekBytes := argon2.IDKey([]byte(passphrase), salt, 3, 65536, 1, 32)

	// Wrap DB KEK
	wrapDbAad, _ := aad.BuildWrapKeyV1("wrap-database-key-v1", dbKid, unlockKid)
	wrapDbNonce := bytesOf(12, 0xaa)
	wrappedDbKek := encryptAEAD(t, unlockKekBytes, wrapDbNonce, dbKek, wrapDbAad)
	wrapId1 := "77777777-7777-4777-8777-777777777777"
	_, err = db.Exec("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
		wrapId1, dbKid, unlockKid, 1, "key_wrap", "A256GCM", wrapDbNonce, wrappedDbKek, "wrap-database-key-v1", nowMs)
	if err != nil {
		t.Fatalf("failed to insert wrapped db kek: %v", err)
	}

	// Wrap Record DEK
	wrapRecAad, _ := aad.BuildWrapKeyV1("wrap-record-key-v1", recordKid, dbKid)
	wrapRecNonce := bytesOf(12, 0xbb)
	wrappedRecDek := encryptAEAD(t, dbKek, wrapRecNonce, recordDek, wrapRecAad)
	wrapId2 := "88888888-8888-4888-8888-888888888888"
	_, err = db.Exec("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
		wrapId2, recordKid, dbKid, 1, "key_wrap", "A256GCM", wrapRecNonce, wrappedRecDek, "wrap-record-key-v1", nowMs)
	if err != nil {
		t.Fatalf("failed to insert wrapped rec dek: %v", err)
	}

	// Encrypted Object
	payload := map[string]interface{}{"hello": "world", "v": 1}
	payloadJcs, _ := jcs.Canonicalize(payload)
	payloadAad, _ := aad.BuildRecordPayloadV1(objectUuid, schemaUuid, "application/json", recordKid, "A256GCM")
	payloadNonce := bytesOf(12, 0xcc)
	ciphertext := encryptAEAD(t, recordDek, payloadNonce, []byte(payloadJcs), payloadAad)

	_, err = db.Exec("INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
		objectUuid, 1, "aead", schemaUuid, "application/json", "A256GCM", recordKid, payloadNonce, ciphertext, "record-payload-v1", nowMs, nowMs)
	if err != nil {
		t.Fatalf("failed to insert object: %v", err)
	}

	return dbPath, objectUuid
}

func insertKey(t *testing.T, db *sql.DB, kid, class, purpose, alg, status string, timeMs int64) {
	_, err := db.Exec("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
		kid, class, purpose, alg, status, timeMs)
	if err != nil {
		t.Fatalf("failed to insert key %s: %v", kid, err)
	}
}

func bytesOf(n int, val byte) []byte {
	b := make([]byte, n)
	for i := range b {
		b[i] = val
	}
	return b
}

func encryptAEAD(t *testing.T, key, nonce, pt, aad []byte) []byte {
	block, err := aes.NewCipher(key)
	if err != nil {
		t.Fatalf("aes err: %v", err)
	}
	aesgcm, err := cipher.NewGCM(block)
	if err != nil {
		t.Fatalf("gcm err: %v", err)
	}
	return aesgcm.Seal(nil, nonce, pt, aad)
}

func TestReader_Valid(t *testing.T) {
	tmpDir := t.TempDir()
	dbPath := filepath.Join(tmpDir, "test.db")
	passphrase := "my-secret-pass"
	_, objUuid := createTestDB(t, dbPath, passphrase)

	reader, err := OpenReadOnly(dbPath, passphrase)
	if err != nil {
		t.Fatalf("OpenReadOnly failed: %v", err)
	}
	defer reader.Close()

	payload, err := reader.DecryptObject(objUuid)
	if err != nil {
		t.Fatalf("DecryptObject failed: %v", err)
	}

	expectedJcs := `{"hello":"world","v":1}`
	if string(payload) != expectedJcs {
		t.Errorf("Expected %s, got %s", expectedJcs, string(payload))
	}

	// Verify valid JSON
	var dummy map[string]interface{}
	if err := json.Unmarshal(payload, &dummy); err != nil {
		t.Errorf("Failed to unmarshal returned payload: %v", err)
	}
}

func TestReader_WrongPassphrase(t *testing.T) {
	tmpDir := t.TempDir()
	dbPath := filepath.Join(tmpDir, "test.db")
	passphrase := "my-secret-pass"
	createTestDB(t, dbPath, passphrase)

	_, err := OpenReadOnly(dbPath, "wrong-pass")
	if err == nil {
		t.Fatal("Expected error for wrong passphrase, got nil")
	}
	if !strings.Contains(err.Error(), "authentication failure") {
		t.Errorf("Expected auth failure error, got: %v", err)
	}
}

func TestReader_ObjectNotFound(t *testing.T) {
	tmpDir := t.TempDir()
	dbPath := filepath.Join(tmpDir, "test.db")
	passphrase := "my-secret-pass"
	createTestDB(t, dbPath, passphrase)

	reader, err := OpenReadOnly(dbPath, passphrase)
	if err != nil {
		t.Fatalf("OpenReadOnly failed: %v", err)
	}
	defer reader.Close()

	_, err = reader.DecryptObject("99999999-9999-4999-8999-999999999999")
	if err == nil {
		t.Fatal("Expected error for missing object, got nil")
	}
	if !strings.Contains(err.Error(), "object not found") {
		t.Errorf("Expected not found error, got: %v", err)
	}
}
