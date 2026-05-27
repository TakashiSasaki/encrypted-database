package sqlitev1

import (
	"crypto/aes"
	"crypto/cipher"
	"crypto/rand"
	"database/sql"
	"encoding/base64"
	"errors"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/aad"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"github.com/google/uuid"
	"golang.org/x/crypto/argon2"
	_ "modernc.org/sqlite"
)

func generateUUID() string {
	u := uuid.New()
	// google/uuid v4 produces canonical lowercase RFC4122 UUIDs (variant 8/9/a/b).
	return u.String()
}

type Writer struct {
	db          *sql.DB
	activeDbKek []byte
	activeDbKid string
}

func generateRandomBytes(n int) ([]byte, error) {
	b := make([]byte, n)
	_, err := rand.Read(b)
	if err != nil {
		return nil, err
	}
	return b, nil
}

func isValidContentType(contentType string) bool {
	if contentType == "" || strings.IndexByte(contentType, '/') <= 0 || strings.HasSuffix(contentType, "/") {
		return false
	}
	for _, r := range contentType {
		if r < 0x20 || r == 0x7f {
			return false
		}
	}
	return true
}

func loadSchemaSQL() (string, error) {
	path := os.Getenv("VAULT_SCHEMA_SQL_PATH")
	if path == "" {
		// Try to find the docs directory from the current working directory.
		// For tests it could be nested.
		// As a fallback, we assume we are running from the repository root.
		path = "docs/backend/sqlite/schema.sql"
		if _, err := os.Stat(path); os.IsNotExist(err) {
			path = "../docs/backend/sqlite/schema.sql"
		}
		if _, err := os.Stat(path); os.IsNotExist(err) {
			path = "../../docs/backend/sqlite/schema.sql"
		}
		if _, err := os.Stat(path); os.IsNotExist(err) {
			path = "../../../docs/backend/sqlite/schema.sql"
		}
	}
	b, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(b), nil
}

func CreateNew(path string, passphrase string, platform string) (*Writer, error) {
	if passphrase == "" {
		return nil, errors.New("passphrase must be a non-empty string")
	}

	schemaSQL, err := loadSchemaSQL()
	if err != nil {
		return nil, fmt.Errorf("failed to load schema: %w", err)
	}

	db, err := sql.Open("sqlite", path)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	// PRAGMA foreign_keys = ON should be set before any transactions
	_, err = db.Exec("PRAGMA foreign_keys = ON")
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to set PRAGMA foreign_keys: %w", err)
	}

	tx, err := db.Begin()
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to begin transaction: %w", err)
	}

	var activeDbKek []byte
	var activeDbKid string

	commitOrRollback := func() error {
		defer tx.Rollback()

		// Bootstrap schema within transaction to ensure full cleanup on failure
		_, err = tx.Exec(schemaSQL)
		if err != nil {
			return fmt.Errorf("failed to execute schema: %w", err)
		}
		_, err = tx.Exec("PRAGMA application_id = 1447906135")
		if err != nil {
			return fmt.Errorf("failed to set PRAGMA application_id: %w", err)
		}
		_, err = tx.Exec("PRAGMA user_version = 1")
		if err != nil {
			return fmt.Errorf("failed to set PRAGMA user_version: %w", err)
		}

		// Validate platform
		var p string
		err = tx.QueryRow("SELECT platform FROM platform_tbl WHERE platform = ?", platform).Scan(&p)
		if err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return fmt.Errorf("unsupported platform: %s", platform)
			}
			return fmt.Errorf("failed to validate platform: %w", err)
		}

		dbKekBytes, err := generateRandomBytes(32)
		if err != nil {
			return err
		}
		dbKid := generateUUID()
		activeDbKek = dbKekBytes
		activeDbKid = dbKid

		salt, err := generateRandomBytes(16)
		if err != nil {
			return err
		}

		unlockKekBytes := argon2.IDKey([]byte(passphrase), salt, 3, 65536, 1, 32)
		unlockKid := generateUUID()

		saltB64 := base64.RawURLEncoding.EncodeToString(salt)
		providerConfig := map[string]interface{}{
			"kdf":          "argon2id",
			"profile":      "argon2id-profile-v1",
			"salt":         saltB64,
			"memory_kib":   65536,
			"iterations":   3,
			"parallelism":  1,
			"output_bytes": 32,
		}

		providerConfigJson, err := jcs.Canonicalize(providerConfig)
		if err != nil {
			return fmt.Errorf("failed to canonicalize provider config: %w", err)
		}

		wrapAlg := "A256GCM"
		aadPolicyName := "wrap-database-key-v1"
		aadBytes, err := aad.BuildWrapKeyV1(aadPolicyName, dbKid, unlockKid)
		if err != nil {
			return fmt.Errorf("failed to build wrap key AAD: %w", err)
		}

		nonce, err := generateRandomBytes(12)
		if err != nil {
			return err
		}

		block, err := aes.NewCipher(unlockKekBytes)
		if err != nil {
			return err
		}
		aesgcm, err := cipher.NewGCM(block)
		if err != nil {
			return err
		}
		wrappedDbKek := aesgcm.Seal(nil, nonce, dbKekBytes, aadBytes)

		dbUuid := generateUUID()
		nowMs := time.Now().UnixMilli()

		metadata := map[string]string{
			"storage_format_id":     "vault.moukaeritai.work.storage",
			"format_major":          "1",
			"format_minor":          "0",
			"schema_version":        "1",
			"database_uuid":         dbUuid,
			"created_at_ms":         fmt.Sprintf("%d", nowMs),
			"created_by_library":    "vault-go",
			"created_by_version":    "0.0.0-dev",
			"sqlite_application_id": "1447906135",
			"sqlite_user_version":   "1",
			"required_features":     "[]",
			"optional_features":     "[]",
		}

		for prop, val := range metadata {
			_, err = tx.Exec("INSERT INTO storage_metadata_tbl (property, value) VALUES (?, ?)", prop, val)
			if err != nil {
				return err
			}
		}

		_, err = tx.Exec("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", dbKid, "database_kek", "wrap_record_keys", wrapAlg, "active", nowMs)
		if err != nil {
			return err
		}
		_, err = tx.Exec("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", unlockKid, "unlock_kek", "wrap_database_keys", wrapAlg, "active", nowMs)
		if err != nil {
			return err
		}
		_, err = tx.Exec("INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)", unlockKid, "passphrase_argon2id", providerConfigJson, platform)
		if err != nil {
			return err
		}
		wrapId := generateUUID()
		_, err = tx.Exec("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", wrapId, dbKid, unlockKid, 1, "key_wrap", wrapAlg, nonce, wrappedDbKek, aadPolicyName, nowMs)
		if err != nil {
			return err
		}

		return tx.Commit()
	}

	if err := commitOrRollback(); err != nil {
		db.Close()
		return nil, err
	}

	return &Writer{
		db:          db,
		activeDbKek: activeDbKek,
		activeDbKid: activeDbKid,
	}, nil
}

func (w *Writer) Close() error {
	if w.db != nil {
		return w.db.Close()
	}
	return nil
}

func (w *Writer) StorePayload(schemaUUID string, contentType string, payload any) (string, error) {
	if w.activeDbKek == nil {
		return "", errors.New("database is locked")
	}
	if !uuidRegex.MatchString(schemaUUID) {
		return "", errors.New("invalid schemaUUID")
	}

	if !isValidContentType(contentType) {
		return "", errors.New("invalid content type")
	}

	objectUUID := generateUUID()
	recordDekBytes, err := generateRandomBytes(32)
	if err != nil {
		return "", err
	}
	recordKid := generateUUID()
	alg := "A256GCM"

	wrapAadPolicy := "wrap-record-key-v1"
	wrapAadBytes, err := aad.BuildWrapKeyV1(wrapAadPolicy, recordKid, w.activeDbKid)
	if err != nil {
		return "", err
	}

	nonceWrap, err := generateRandomBytes(12)
	if err != nil {
		return "", err
	}
	blockWrap, err := aes.NewCipher(w.activeDbKek)
	if err != nil {
		return "", err
	}
	aesgcmWrap, err := cipher.NewGCM(blockWrap)
	if err != nil {
		return "", err
	}
	wrappedRecordDek := aesgcmWrap.Seal(nil, nonceWrap, recordDekBytes, wrapAadBytes)

	payloadStr, err := jcs.Canonicalize(payload)
	if err != nil {
		return "", fmt.Errorf("failed to canonicalize payload: %w", err)
	}
	payloadBytes := []byte(payloadStr)

	payloadAadPolicy := "record-payload-v1"
	payloadAadBytes, err := aad.BuildRecordPayloadV1(objectUUID, schemaUUID, contentType, recordKid, alg)
	if err != nil {
		return "", err
	}

	noncePayload, err := generateRandomBytes(12)
	if err != nil {
		return "", err
	}
	blockPayload, err := aes.NewCipher(recordDekBytes)
	if err != nil {
		return "", err
	}
	aesgcmPayload, err := cipher.NewGCM(blockPayload)
	if err != nil {
		return "", err
	}
	ciphertext := aesgcmPayload.Seal(nil, noncePayload, payloadBytes, payloadAadBytes)

	tx, err := w.db.Begin()
	if err != nil {
		return "", err
	}
	defer tx.Rollback()

	nowMs := time.Now().UnixMilli()

	_, err = tx.Exec("INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)", recordKid, "record_dek", "encrypt_payload", alg, "active", nowMs)
	if err != nil {
		return "", err
	}

	wrapId := generateUUID()
	_, err = tx.Exec("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", wrapId, recordKid, w.activeDbKid, 1, "key_wrap", alg, nonceWrap, wrappedRecordDek, wrapAadPolicy, nowMs)
	if err != nil {
		return "", err
	}

	_, err = tx.Exec("INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", objectUUID, 1, "aead", schemaUUID, contentType, alg, recordKid, noncePayload, ciphertext, payloadAadPolicy, nowMs, nowMs)
	if err != nil {
		return "", err
	}

	if err := tx.Commit(); err != nil {
		return "", err
	}

	return objectUUID, nil
}

func (w *Writer) UpdatePayload(objectUUID string, schemaUUID string, contentType string, payload any) error {
	if w.activeDbKek == nil {
		return errors.New("database is locked")
	}
	if !uuidRegex.MatchString(objectUUID) {
		return errors.New("invalid objectUUID")
	}
	if !uuidRegex.MatchString(schemaUUID) {
		return errors.New("invalid schemaUUID")
	}
	if !isValidContentType(contentType) {
		return errors.New("invalid content type")
	}

	tx, err := w.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	var recordKid, alg string
	var createdAtMs int64
	err = tx.QueryRow("SELECT kid, alg, created_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?", objectUUID).Scan(&recordKid, &alg, &createdAtMs)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("%w: object %s", ErrNotFound, objectUUID)
		}
		return err
	}
	if alg != "A256GCM" {
		return errors.New("unsupported object alg")
	}
	var recordDekStatus string
	err = tx.QueryRow("SELECT status FROM key_tbl WHERE kid = ? AND key_class = 'record_dek'", recordKid).Scan(&recordDekStatus)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("%w: record DEK %s not found", ErrNotFound, recordKid)
		}
		return fmt.Errorf("failed to query record DEK status: %w", err)
	}
	if recordDekStatus != "active" {
		return fmt.Errorf("%w: record DEK status must be active", ErrInvalidStatus)
	}

	var envelopeV int64
	var envelopeType, wrapAlg, wrapAadPolicy string
	var nonceWrap, wrappedRecordDek []byte
	err = tx.QueryRow("SELECT envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?",
		recordKid, w.activeDbKid).Scan(&envelopeV, &envelopeType, &wrapAlg, &nonceWrap, &wrappedRecordDek, &wrapAadPolicy)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("%w: record DEK wrap info not found", ErrNotFound)
		}
		return err
	}
	if envelopeV != 1 || envelopeType != "key_wrap" || wrapAlg != "A256GCM" || wrapAadPolicy != "wrap-record-key-v1" {
		return errors.New("invalid wrapped key envelope metadata")
	}

	wrapAadBytes, err := aad.BuildWrapKeyV1(wrapAadPolicy, recordKid, w.activeDbKid)
	if err != nil {
		return err
	}
	blockWrap, err := aes.NewCipher(w.activeDbKek)
	if err != nil {
		return err
	}
	aesgcmWrap, err := cipher.NewGCM(blockWrap)
	if err != nil {
		return err
	}
	recordDekBytes, err := aesgcmWrap.Open(nil, nonceWrap, wrappedRecordDek, wrapAadBytes)
	if err != nil {
		return err
	}

	payloadStr, err := jcs.Canonicalize(payload)
	if err != nil {
		return fmt.Errorf("failed to canonicalize payload: %w", err)
	}
	payloadAadPolicy := "record-payload-v1"
	payloadAadBytes, err := aad.BuildRecordPayloadV1(objectUUID, schemaUUID, contentType, recordKid, "A256GCM")
	if err != nil {
		return err
	}
	noncePayload, err := generateRandomBytes(12)
	if err != nil {
		return err
	}
	blockPayload, err := aes.NewCipher(recordDekBytes)
	if err != nil {
		return err
	}
	aesgcmPayload, err := cipher.NewGCM(blockPayload)
	if err != nil {
		return err
	}
	ciphertext := aesgcmPayload.Seal(nil, noncePayload, []byte(payloadStr), payloadAadBytes)
	nowMs := time.Now().UnixMilli()

	_, err = tx.Exec("UPDATE encrypted_object_tbl SET schema_uuid = ?, content_type = ?, nonce = ?, ciphertext = ?, aad_policy = ?, updated_at_ms = ?, created_at_ms = ? WHERE object_uuid = ?",
		schemaUUID, contentType, noncePayload, ciphertext, payloadAadPolicy, nowMs, createdAtMs, objectUUID)
	if err != nil {
		return err
	}
	return tx.Commit()
}

func (w *Writer) DeletePayload(objectUUID string) error {
	if w.activeDbKek == nil {
		return errors.New("database is locked")
	}
	if !uuidRegex.MatchString(objectUUID) {
		return errors.New("invalid objectUUID")
	}
	tx, err := w.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()
	res, err := tx.Exec("DELETE FROM encrypted_object_tbl WHERE object_uuid = ?", objectUUID)
	if err != nil {
		return err
	}
	n, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if n == 0 {
		return fmt.Errorf("%w: object %s", ErrNotFound, objectUUID)
	}
	return tx.Commit()
}
