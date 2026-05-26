package sqlitev1

import (
	"crypto/aes"
	"crypto/cipher"
	"database/sql"
	"encoding/json"
	"errors"
	"fmt"
	"net/url"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/aad"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/base64url"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"golang.org/x/crypto/argon2"
)

var (
	ErrInvalidFormat         = errors.New("invalid storage format")
	ErrInvalidProviderConfig = errors.New("invalid provider config")
	ErrUnsupported           = errors.New("unsupported provider or algorithm")
	ErrAuthFailure           = errors.New("authentication failure")
	ErrNotFound              = errors.New("not found")
	ErrInvalidStatus         = errors.New("invalid key status")
	ErrInvalidEnvelope       = errors.New("invalid envelope")
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

	// Properly escape path for SQLite URI to avoid injection or breaking on '#' / '?'
	parsedURL := &url.URL{
		Scheme: "file",
		Opaque: url.PathEscape(path),
	}
	q := parsedURL.Query()
	q.Set("mode", "ro")
	parsedURL.RawQuery = q.Encode()

	db, err := sql.Open("sqlite", parsedURL.String())
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

func validateArgon2idConfig(providerConfigJson string) ([]byte, error) {
	var config map[string]interface{}
	if err := json.Unmarshal([]byte(providerConfigJson), &config); err != nil {
		return nil, fmt.Errorf("%w: provider_config_json is not valid JSON", ErrInvalidProviderConfig)
	}

	canonicalConfig, err := jcs.Canonicalize(config)
	if err != nil {
		return nil, fmt.Errorf("%w: failed to canonicalize provider config", ErrInvalidProviderConfig)
	}
	if canonicalConfig != providerConfigJson {
		return nil, fmt.Errorf("%w: provider_config_json is not valid JCS canonical JSON", ErrInvalidProviderConfig)
	}

	kdf, okKdf := config["kdf"].(string)
	profile, okProfile := config["profile"].(string)

	if !okKdf || !okProfile {
		return nil, fmt.Errorf("%w: missing required provider config property or invalid type", ErrInvalidProviderConfig)
	}

	if kdf != "argon2id" || profile != "argon2id-profile-v1" {
		return nil, fmt.Errorf("%w: unsupported provider or profile", ErrUnsupported)
	}

	memKib, ok1 := config["memory_kib"].(float64)
	iter, ok2 := config["iterations"].(float64)
	parallelism, ok3 := config["parallelism"].(float64)
	outBytes, ok4 := config["output_bytes"].(float64)
	saltB64, ok5 := config["salt"].(string)

	if !ok1 || !ok2 || !ok3 || !ok4 || !ok5 {
		return nil, fmt.Errorf("%w: missing required provider config property or invalid type", ErrInvalidProviderConfig)
	}

	if memKib != 65536 || iter != 3 || parallelism != 1 || outBytes != 32 {
		return nil, fmt.Errorf("%w: immutable profile-v1 parameter mismatch", ErrInvalidProviderConfig)
	}

	salt, err := base64url.DecodeStrict(saltB64)
	if err != nil {
		return nil, fmt.Errorf("%w: salt decode error", ErrInvalidProviderConfig)
	}
	if len(salt) != 16 {
		return nil, fmt.Errorf("%w: salt length must be 16 bytes", ErrInvalidProviderConfig)
	}

	return salt, nil
}

func (r *Reader) unlockDatabase(passphrase string) error {
	var dbKid string
	err := r.db.QueryRow("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1").Scan(&dbKid)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("%w: no active database KEK found", ErrInvalidStatus)
		}
		return fmt.Errorf("failed to query database KEK: %w", err)
	}

	rows, err := r.db.Query("SELECT wrapping_kid, nonce, wrapped_key, aad_policy, wrap_alg, envelope_v, envelope_type FROM wrapped_key_tbl WHERE wrapped_kid = ?", dbKid)
	if err != nil {
		return fmt.Errorf("failed to query wrapped database keys: %w", err)
	}
	defer rows.Close()

	unwrapped := false
	for rows.Next() {
		var wrappingKid, aadPolicyName, wrapAlg, envelopeType string
		var nonce, wrappedKey []byte
		var envelopeV int
		if err := rows.Scan(&wrappingKid, &nonce, &wrappedKey, &aadPolicyName, &wrapAlg, &envelopeV, &envelopeType); err != nil {
			return fmt.Errorf("failed to scan wrapped key row: %w", err)
		}

		// The initial read-only reader treats unsupported database_kek wrap metadata or unsupported unlock providers as explicit
		// format/compatibility errors instead of silently skipping rows. Multi-provider fallback semantics can be revisited
		// when additional unlock providers are implemented.
		if wrapAlg != "A256GCM" {
			return fmt.Errorf("%w: unsupported wrap algorithm %s", ErrUnsupported, wrapAlg)
		}
		if envelopeV != 1 {
			return fmt.Errorf("%w: unsupported envelope version %d", ErrUnsupported, envelopeV)
		}
		if envelopeType != "key_wrap" {
			return fmt.Errorf("%w: unsupported envelope type %s", ErrUnsupported, envelopeType)
		}
		if len(nonce) != 12 {
			return fmt.Errorf("%w: wrap nonce length %d", ErrInvalidEnvelope, len(nonce))
		}
		if len(wrappedKey) < 16 {
			return fmt.Errorf("%w: wrapped key length %d", ErrInvalidEnvelope, len(wrappedKey))
		}

		var unlockProvider, providerConfigJson string
		err = r.db.QueryRow("SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?", wrappingKid).Scan(&unlockProvider, &providerConfigJson)
		if err != nil {
			if errors.Is(err, sql.ErrNoRows) {
				return fmt.Errorf("%w: missing unlock provider row", ErrAuthFailure)
			}
			return fmt.Errorf("failed to query unlock KEK: %w", err)
		}

		if unlockProvider != "passphrase_argon2id" {
			return fmt.Errorf("%w: unsupported unlock provider %s", ErrUnsupported, unlockProvider)
		}

		salt, err := validateArgon2idConfig(providerConfigJson)
		if err != nil {
			return err // Return directly since validateArgon2idConfig already wraps properly
		}

		unlockKek := argon2.IDKey([]byte(passphrase), salt, 3, 65536, 1, 32)

		wrapAad, err := aad.BuildWrapKeyV1(aadPolicyName, dbKid, wrappingKid)
		if err != nil {
			// e.g. unsupported aad_policy returns ErrUnsupported from BuildWrapKeyV1 (which we might map or just return)
			// Actually BuildWrapKeyV1 returns `fmt.Errorf("unsupported AAD policy: %s", policyName)` but doesn't wrap ErrUnsupported.
			// Let's explicitly check and return ErrUnsupported.
			return fmt.Errorf("%w: %v", ErrUnsupported, err)
		}

		dbKekBytes, err := r.decryptAEAD(unlockKek, nonce, wrappedKey, wrapAad)
		if err == nil {
			if len(dbKekBytes) != 32 {
				return fmt.Errorf("%w: unwrapped database KEK must be 32 bytes", ErrInvalidEnvelope)
			}
			r.activeDbKek = dbKekBytes
			r.activeDbKid = dbKid
			unwrapped = true
			break
		}
	}
	if err := rows.Err(); err != nil {
		return fmt.Errorf("wrapped key rows iteration error: %w", err)
	}

	if !unwrapped {
		return fmt.Errorf("%w: wrong passphrase or decryption failed", ErrAuthFailure)
	}

	return nil
}

func (r *Reader) DecryptObject(objectUUID string) ([]byte, error) {
	if r.activeDbKek == nil {
		return nil, fmt.Errorf("%w: database is locked or uninitialized", ErrAuthFailure)
	}

	var schemaUUID, contentType, alg, recordKid, payloadAadPolicy string
	var noncePayload, ciphertext []byte

	err := r.db.QueryRow("SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?", objectUUID).
		Scan(&schemaUUID, &contentType, &alg, &recordKid, &noncePayload, &ciphertext, &payloadAadPolicy)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("%w: object %s", ErrNotFound, objectUUID)
		}
		return nil, fmt.Errorf("failed to query encrypted object: %w", err)
	}

	if alg != "A256GCM" {
		return nil, fmt.Errorf("%w: payload algorithm %s", ErrUnsupported, alg)
	}
	if payloadAadPolicy != "record-payload-v1" {
		return nil, fmt.Errorf("%w: payload aad_policy %s", ErrUnsupported, payloadAadPolicy)
	}
	if len(noncePayload) != 12 {
		return nil, fmt.Errorf("%w: payload nonce length %d", ErrInvalidEnvelope, len(noncePayload))
	}
	if len(ciphertext) < 16 {
		return nil, fmt.Errorf("%w: payload ciphertext length %d", ErrInvalidEnvelope, len(ciphertext))
	}

	var recordDekStatus string
	err = r.db.QueryRow("SELECT status FROM key_tbl WHERE kid = ? AND key_class = 'record_dek'", recordKid).Scan(&recordDekStatus)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("%w: record DEK %s not found", ErrNotFound, recordKid)
		}
		return nil, fmt.Errorf("failed to query record DEK status: %w", err)
	}
	if recordDekStatus != "active" {
		return nil, fmt.Errorf("%w: record DEK status must be active", ErrInvalidStatus)
	}

	var nonceWrap, wrappedRecordDek []byte
	var wrapAadPolicy, wrapAlg, envelopeType string
	var envelopeV int
	err = r.db.QueryRow("SELECT nonce, wrapped_key, aad_policy, wrap_alg, envelope_v, envelope_type FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?", recordKid, r.activeDbKid).
		Scan(&nonceWrap, &wrappedRecordDek, &wrapAadPolicy, &wrapAlg, &envelopeV, &envelopeType)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, fmt.Errorf("%w: record DEK wrap info not found", ErrNotFound)
		}
		return nil, fmt.Errorf("failed to query record DEK: %w", err)
	}

	if wrapAlg != "A256GCM" {
		return nil, fmt.Errorf("%w: wrap algorithm %s", ErrUnsupported, wrapAlg)
	}
	if envelopeV != 1 {
		return nil, fmt.Errorf("%w: envelope version %d", ErrUnsupported, envelopeV)
	}
	if envelopeType != "key_wrap" {
		return nil, fmt.Errorf("%w: envelope type %s", ErrUnsupported, envelopeType)
	}
	if len(nonceWrap) != 12 {
		return nil, fmt.Errorf("%w: wrap nonce length %d", ErrInvalidEnvelope, len(nonceWrap))
	}
	if len(wrappedRecordDek) < 16 {
		return nil, fmt.Errorf("%w: wrapped key length %d", ErrInvalidEnvelope, len(wrappedRecordDek))
	}

	wrapAadBytes, err := aad.BuildWrapKeyV1(wrapAadPolicy, recordKid, r.activeDbKid)
	if err != nil {
		return nil, fmt.Errorf("failed to build record DEK wrap AAD: %w", err)
	}

	recordDekBytes, err := r.decryptAEAD(r.activeDbKek, nonceWrap, wrappedRecordDek, wrapAadBytes)
	if err != nil {
		return nil, fmt.Errorf("%w: failed to unwrap record DEK", ErrAuthFailure)
	}
	if len(recordDekBytes) != 32 {
		return nil, fmt.Errorf("%w: unwrapped record DEK must be 32 bytes", ErrInvalidEnvelope)
	}

	payloadAadBytes, err := aad.BuildRecordPayloadV1(objectUUID, schemaUUID, contentType, recordKid, alg)
	if err != nil {
		return nil, fmt.Errorf("failed to build payload AAD: %w", err)
	}

	payloadBytes, err := r.decryptAEAD(recordDekBytes, noncePayload, ciphertext, payloadAadBytes)
	if err != nil {
		return nil, fmt.Errorf("%w: failed to decrypt payload", ErrAuthFailure)
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
	if len(nonce) != aesgcm.NonceSize() {
		return nil, fmt.Errorf("%w: invalid nonce size: expected %d, got %d", ErrInvalidEnvelope, aesgcm.NonceSize(), len(nonce))
	}
	return aesgcm.Open(nil, nonce, ciphertextAndTag, aadData)
}
