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

	// Bootstrap schema
	_, err = db.Exec(schemaSQL)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to execute schema: %w", err)
	}
	_, err = db.Exec("PRAGMA application_id = 1447906135")
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to set PRAGMA application_id: %w", err)
	}
	_, err = db.Exec("PRAGMA user_version = 1")
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to set PRAGMA user_version: %w", err)
	}
	_, err = db.Exec("PRAGMA foreign_keys = ON")
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to set PRAGMA foreign_keys: %w", err)
	}

	// Validate platform
	var p string
	err = db.QueryRow("SELECT platform FROM platform_tbl WHERE platform = ?", platform).Scan(&p)
	if err != nil {
		db.Close()
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("unsupported platform: %s", platform)
		}
		return nil, fmt.Errorf("failed to validate platform: %w", err)
	}

	dbKekBytes, err := generateRandomBytes(32)
	if err != nil {
		db.Close()
		return nil, err
	}
	dbKid := uuid.New().String()

	salt, err := generateRandomBytes(16)
	if err != nil {
		db.Close()
		return nil, err
	}

	unlockKekBytes := argon2.IDKey([]byte(passphrase), salt, 3, 65536, 1, 32)
	unlockKid := uuid.New().String()

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
		db.Close()
		return nil, fmt.Errorf("failed to canonicalize provider config: %w", err)
	}

	wrapAlg := "A256GCM"
	aadPolicyName := "wrap-database-key-v1"
	aadBytes, err := aad.BuildWrapKeyV1(aadPolicyName, dbKid, unlockKid)
	if err != nil {
		db.Close()
		return nil, fmt.Errorf("failed to build wrap key AAD: %w", err)
	}

	nonce, err := generateRandomBytes(12)
	if err != nil {
		db.Close()
		return nil, err
	}

	block, err := aes.NewCipher(unlockKekBytes)
	if err != nil {
		db.Close()
		return nil, err
	}
	aesgcm, err := cipher.NewGCM(block)
	if err != nil {
		db.Close()
		return nil, err
	}
	wrappedDbKek := aesgcm.Seal(nil, nonce, dbKekBytes, aadBytes)

	tx, err := db.Begin()
	if err != nil {
		db.Close()
		return nil, err
	}

	commitOrRollback := func() error {
		defer tx.Rollback()
		dbUuid := uuid.New().String()
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
		wrapId := uuid.New().String()
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
		activeDbKek: dbKekBytes,
		activeDbKid: dbKid,
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
	if contentType == "" || !strings.Contains(contentType, "/") {
		return "", errors.New("invalid content type")
	}

	objectUUID := uuid.New().String()
	recordDekBytes, err := generateRandomBytes(32)
	if err != nil {
		return "", err
	}
	recordKid := uuid.New().String()
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
		return "", err
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

	wrapId := uuid.New().String()
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
