package sqlitev1

import (
	"crypto/aes"
	"crypto/cipher"
	"database/sql"
	"errors"
	"fmt"
	"strings"
	"time"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/aad"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
)

// decryptAEAD is copied from reader.go so writer can use it without changing reader.go.
func decryptAEAD(key []byte, nonce []byte, ciphertextAndTag []byte, aadData []byte) ([]byte, error) {
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
	if contentType == "" || !strings.Contains(contentType, "/") {
		return errors.New("invalid content type")
	}

	var recordKid, alg string
	err := w.db.QueryRow("SELECT kid, alg FROM encrypted_object_tbl WHERE object_uuid = ?", objectUUID).Scan(&recordKid, &alg)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("%w: object %s", ErrNotFound, objectUUID)
		}
		return fmt.Errorf("failed to query object: %w", err)
	}

	if alg != "A256GCM" {
		return fmt.Errorf("%w: unsupported payload algorithm %s", ErrUnsupported, alg)
	}

	var nonceWrap, wrappedRecordDek []byte
	var wrapAadPolicy, wrapAlg, envelopeType string
	var envelopeV int
	err = w.db.QueryRow("SELECT nonce, wrapped_key, aad_policy, wrap_alg, envelope_v, envelope_type FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?", recordKid, w.activeDbKid).
		Scan(&nonceWrap, &wrappedRecordDek, &wrapAadPolicy, &wrapAlg, &envelopeV, &envelopeType)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return fmt.Errorf("%w: record DEK wrap info not found", ErrNotFound)
		}
		return fmt.Errorf("failed to query record DEK: %w", err)
	}

	if wrapAlg != "A256GCM" {
		return fmt.Errorf("%w: wrap algorithm %s", ErrUnsupported, wrapAlg)
	}
	if envelopeV != 1 {
		return fmt.Errorf("%w: envelope version %d", ErrUnsupported, envelopeV)
	}
	if envelopeType != "key_wrap" {
		return fmt.Errorf("%w: envelope type %s", ErrUnsupported, envelopeType)
	}
	if len(nonceWrap) != 12 {
		return fmt.Errorf("%w: wrap nonce length %d", ErrInvalidEnvelope, len(nonceWrap))
	}
	if len(wrappedRecordDek) < 16 {
		return fmt.Errorf("%w: wrapped key length %d", ErrInvalidEnvelope, len(wrappedRecordDek))
	}

	wrapAadBytes, err := aad.BuildWrapKeyV1(wrapAadPolicy, recordKid, w.activeDbKid)
	if err != nil {
		return fmt.Errorf("failed to build record DEK wrap AAD: %w", err)
	}

	recordDekBytes, err := decryptAEAD(w.activeDbKek, nonceWrap, wrappedRecordDek, wrapAadBytes)
	if err != nil {
		return fmt.Errorf("%w: failed to unwrap record DEK", ErrAuthFailure)
	}
	if len(recordDekBytes) != 32 {
		return fmt.Errorf("%w: unwrapped record DEK must be 32 bytes", ErrInvalidEnvelope)
	}

	payloadStr, err := jcs.Canonicalize(payload)
	if err != nil {
		return fmt.Errorf("failed to canonicalize payload: %w", err)
	}
	payloadBytes := []byte(payloadStr)

	payloadAadPolicy := "record-payload-v1"
	payloadAadBytes, err := aad.BuildRecordPayloadV1(objectUUID, schemaUUID, contentType, recordKid, alg)
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
	ciphertext := aesgcmPayload.Seal(nil, noncePayload, payloadBytes, payloadAadBytes)

	nowMs := time.Now().UnixMilli()

	tx, err := w.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	res, err := tx.Exec("UPDATE encrypted_object_tbl SET schema_uuid = ?, content_type = ?, nonce = ?, ciphertext = ?, aad_policy = ?, updated_at_ms = ? WHERE object_uuid = ?",
		schemaUUID, contentType, noncePayload, ciphertext, payloadAadPolicy, nowMs, objectUUID)
	if err != nil {
		return err
	}

	rowsAffected, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if rowsAffected == 0 {
		return fmt.Errorf("%w: object %s not found during update", ErrNotFound, objectUUID)
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

	rowsAffected, err := res.RowsAffected()
	if err != nil {
		return err
	}
	if rowsAffected == 0 {
		return fmt.Errorf("%w: object %s", ErrNotFound, objectUUID)
	}

	return tx.Commit()
}
