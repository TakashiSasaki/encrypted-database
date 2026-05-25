package sqlitev1

import (
	"crypto/aes"
	"crypto/cipher"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/aad"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/base64url"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"golang.org/x/crypto/argon2"
)

type Reader struct {
	db          *sql.DB
	activeDbKek []byte
	activeDbKid string
}

func OpenReadOnly(path string, passphrase string) (*Reader, error) {
	valRes, err := ValidateReadOnly(path)
	if err != nil {
		return nil, fmt.Errorf("metadata validation failed: %w", err)
	}
	_ = valRes // For now we just need it to pass

	dsn := fmt.Sprintf("file:%s?mode=ro", path)
	db, err := sql.Open("sqlite", dsn)
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}

	r := &Reader{
		db: db,
	}

	err = r.unlockDatabase(passphrase)
	if err != nil {
		r.Close()
		return nil, err
	}

	return r, nil
}

func (r *Reader) Close() error {
	if r.db != nil {
		err := r.db.Close()
		r.db = nil
		return err
	}
	return nil
}

func (r *Reader) unlockDatabase(passphrase string) error {
	var dbKid string
	err := r.db.QueryRow("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1").Scan(&dbKid)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return errors.New("no active database KEK found")
		}
		return fmt.Errorf("failed to query database KEK: %w", err)
	}

	rows, err := r.db.Query("SELECT wrapping_kid, nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ?", dbKid)
	if err != nil {
		return fmt.Errorf("failed to query wrapped database keys: %w", err)
	}
	defer rows.Close()

	unwrapped := false
	for rows.Next() {
		var wrappingKid, aadPolicyName string
		var nonce, wrappedKey []byte
		if err := rows.Scan(&wrappingKid, &nonce, &wrappedKey, &aadPolicyName); err != nil {
			return fmt.Errorf("failed to scan wrapped key row: %w", err)
		}

		var unlockProvider, providerConfigJson string
		err = r.db.QueryRow("SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?", wrappingKid).Scan(&unlockProvider, &providerConfigJson)
		if err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				continue
			}
			return fmt.Errorf("failed to query unlock KEK: %w", err)
		}

		if unlockProvider == "passphrase_argon2id" {
			var config map[string]interface{}
			if err := json.Unmarshal([]byte(providerConfigJson), &config); err != nil {
				return errors.New("invalid format: provider_config_json is not valid JSON")
			}

			canonicalConfig, err := jcs.Canonicalize(config)
			if err != nil {
				return fmt.Errorf("failed to canonicalize provider config: %w", err)
			}
			if canonicalConfig != providerConfigJson {
				return errors.New("invalid format: provider_config_json is not valid JCS canonical JSON")
			}

			if config["kdf"] != "argon2id" || config["profile"] != "argon2id-profile-v1" {
				return errors.New("unsupported provider or profile")
			}

			memKib, ok1 := config["memory_kib"].(float64)
			iter, ok2 := config["iterations"].(float64)
			parallelism, ok3 := config["parallelism"].(float64)
			outBytes, ok4 := config["output_bytes"].(float64)
			saltB64, ok5 := config["salt"].(string)

			if !ok1 || !ok2 || !ok3 || !ok4 || !ok5 {
				return errors.New("invalid format: missing required provider config property or invalid type")
			}

			if memKib != 65536 || iter != 3 || parallelism != 1 || outBytes != 32 {
				return errors.New("invalid format: immutable profile-v1 parameter mismatch")
			}

			salt, err := base64url.DecodeStrict(saltB64)
			if err != nil {
				return fmt.Errorf("invalid format: salt decode error: %w", err)
			}
			if len(salt) != 16 {
				return errors.New("invalid format: salt length must be 16 bytes")
			}

			unlockKek := argon2.IDKey([]byte(passphrase), salt, uint32(iter), uint32(memKib), uint8(parallelism), uint32(outBytes))

			wrapAad, err := aad.BuildWrapKeyV1(aadPolicyName, dbKid, wrappingKid)
			if err != nil {
				continue
			}

			dbKekBytes, err := r.decryptAEAD(unlockKek, nonce, wrappedKey, wrapAad)
			if err == nil {
				r.activeDbKek = dbKekBytes
				r.activeDbKid = dbKid
				unwrapped = true
				break
			}
		}
	}
	if err := rows.Err(); err != nil {
		return fmt.Errorf("wrapped key rows iteration error: %w", err)
	}

	if !unwrapped {
		return errors.New("authentication failure: wrong passphrase or decryption failed")
	}

	return nil
}

func (r *Reader) DecryptObject(objectUUID string) ([]byte, error) {
	if r.activeDbKek == nil {
		return nil, errors.New("database is locked or not uninitialized")
	}

	var schemaUUID, contentType, alg, recordKid, payloadAadPolicy string
	var noncePayload, ciphertext []byte

	err := r.db.QueryRow("SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?", objectUUID).
		Scan(&schemaUUID, &contentType, &alg, &recordKid, &noncePayload, &ciphertext, &payloadAadPolicy)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, errors.New("object not found")
		}
		return nil, fmt.Errorf("failed to query encrypted object: %w", err)
	}

	var nonceWrap, wrappedRecordDek []byte
	var wrapAadPolicy string
	err = r.db.QueryRow("SELECT nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?", recordKid, r.activeDbKid).
		Scan(&nonceWrap, &wrappedRecordDek, &wrapAadPolicy)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, errors.New("record DEK wrap info not found")
		}
		return nil, fmt.Errorf("failed to query record DEK: %w", err)
	}

	wrapAadBytes, err := aad.BuildWrapKeyV1(wrapAadPolicy, recordKid, r.activeDbKid)
	if err != nil {
		return nil, fmt.Errorf("failed to build record DEK wrap AAD: %w", err)
	}

	recordDekBytes, err := r.decryptAEAD(r.activeDbKek, nonceWrap, wrappedRecordDek, wrapAadBytes)
	if err != nil {
		return nil, fmt.Errorf("failed to unwrap record DEK: %w", err)
	}

	payloadAadBytes, err := aad.BuildRecordPayloadV1(objectUUID, schemaUUID, contentType, recordKid, alg)
	if err != nil {
		return nil, fmt.Errorf("failed to build payload AAD: %w", err)
	}

	payloadBytes, err := r.decryptAEAD(recordDekBytes, noncePayload, ciphertext, payloadAadBytes)
	if err != nil {
		return nil, fmt.Errorf("failed to decrypt payload: %w", err)
	}

	return payloadBytes, nil
}

func (r *Reader) decryptAEAD(key []byte, nonce []byte, ciphertextAndTag []byte, aadData []byte) ([]byte, error) {
	block, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	aesgcm, err := cipher.NewGCM(block)
	if err != nil {
		return nil, err
	}
	return aesgcm.Open(nil, nonce, ciphertextAndTag, aadData)
}
