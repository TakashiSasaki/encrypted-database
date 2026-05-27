package sqlitev1

import (
	"database/sql"
	"errors"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestWriterRoundtrip(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "vault_writer_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "test.db")
	passphrase := "test-passphrase"

	// 1. Create new database
	writer, err := CreateNew(dbPath, passphrase, "linux")
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}

	// 2. Store payload
	schemaUUID := "00000000-0000-4000-8000-000000000001"
	contentType := "application/json"
	payload := map[string]interface{}{
		"hello": "world",
		"value": 42,
	}

	objUUID, err := writer.StorePayload(schemaUUID, contentType, payload)
	if err != nil {
		t.Fatalf("StorePayload failed: %v", err)
	}
	writer.Close()

	// 3. Open Read Only and Validate
	valRes, err := ValidateReadOnly(dbPath)
	if err != nil {
		t.Fatalf("ValidateReadOnly failed: %v", err)
	}
	if valRes.DatabaseUUID == "" {
		t.Fatalf("expected valid database_uuid")
	}

	reader, err := OpenReadOnly(dbPath, passphrase)
	if err != nil {
		t.Fatalf("OpenReadOnly failed: %v", err)
	}
	defer reader.db.Close()

	// 4. Decrypt object
	decryptedBytes, err := reader.DecryptObject(objUUID)
	if err != nil {
		t.Fatalf("DecryptObject failed: %v", err)
	}

	expectedStr := `{"hello":"world","value":42}`
	if string(decryptedBytes) != expectedStr {
		t.Fatalf("payload mismatch. expected %s, got %s", expectedStr, string(decryptedBytes))
	}

	// 5. Wrong passphrase
	_, err = OpenReadOnly(dbPath, "wrong-passphrase")
	if err == nil {
		t.Fatalf("expected error with wrong passphrase, got nil")
	}
}

func TestWriterNegativeCases(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "vault_writer_negative_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "test.db")
	passphrase := "test-passphrase"

	// Empty passphrase
	_, err = CreateNew(filepath.Join(tempDir, "empty_pass.db"), "", "linux")
	if err == nil {
		t.Fatalf("expected error for empty passphrase")
	}

	// Unknown platform
	_, err = CreateNew(filepath.Join(tempDir, "unknown_platform.db"), passphrase, "unknown_platform")
	if err == nil {
		t.Fatalf("expected error for unknown platform")
	}

	// Valid creation
	writer, err := CreateNew(dbPath, passphrase, "linux")
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}
	defer writer.Close()

	// Invalid schemaUUID
	_, err = writer.StorePayload("invalid-uuid", "application/json", map[string]string{})
	if err == nil {
		t.Fatalf("expected error for invalid schemaUUID")
	}

	// Invalid contentType
	_, err = writer.StorePayload("00000000-0000-4000-8000-000000000001", "invalid", map[string]string{})
	if err == nil {
		t.Fatalf("expected error for invalid contentType")
	}

	// Non-JCS-serializable payload
	// E.g. A map with an unsupported type like func()
	unsupportedPayload := map[string]interface{}{
		"func": func() {},
	}
	_, err = writer.StorePayload("00000000-0000-4000-8000-000000000001", "application/json", unsupportedPayload)
	if err == nil {
		t.Fatalf("expected error for non-JCS-serializable payload")
	}
}

func TestWriterMultiplePayloads(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "vault_writer_multi_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "test.db")
	passphrase := "test-passphrase"

	writer, err := CreateNew(dbPath, passphrase, "linux")
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}
	defer writer.Close()

	schemaUUID := "00000000-0000-4000-8000-000000000001"
	contentType := "application/json"

	var uuids []string
	for i := 0; i < 5; i++ {
		payload := map[string]interface{}{"index": i}
		objUUID, err := writer.StorePayload(schemaUUID, contentType, payload)
		if err != nil {
			t.Fatalf("StorePayload failed at index %d: %v", i, err)
		}
		uuids = append(uuids, objUUID)
	}

	reader, err := OpenReadOnly(dbPath, passphrase)
	if err != nil {
		t.Fatalf("OpenReadOnly failed: %v", err)
	}
	defer reader.db.Close()

	for _, id := range uuids {
		_, err := reader.DecryptObject(id)
		if err != nil {
			t.Fatalf("DecryptObject failed for %s: %v", id, err)
		}
	}
}

func TestWriterUpdatePayloadRoundtripAndTimestamps(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "vault_writer_update_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "test.db")
	passphrase := "test-passphrase"
	writer, err := CreateNew(dbPath, passphrase, "linux")
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}
	defer writer.Close()

	objUUID, err := writer.StorePayload("00000000-0000-4000-8000-000000000001", "application/json", map[string]any{"v": 1})
	if err != nil {
		t.Fatalf("StorePayload failed: %v", err)
	}

	var createdBefore, updatedBefore int64
	err = writer.db.QueryRow(
		"SELECT created_at_ms, updated_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?",
		objUUID,
	).Scan(&createdBefore, &updatedBefore)
	if err != nil {
		t.Fatalf("failed to query pre-update timestamps: %v", err)
	}

	time.Sleep(2 * time.Millisecond)
	err = writer.UpdatePayload(
		objUUID,
		"00000000-0000-4000-8000-000000000002",
		"application/merge-patch+json",
		map[string]any{"hello": "world", "v": 2},
	)
	if err != nil {
		t.Fatalf("UpdatePayload failed: %v", err)
	}

	var createdAfter, updatedAfter int64
	var schemaAfter, contentAfter string
	err = writer.db.QueryRow(
		"SELECT created_at_ms, updated_at_ms, schema_uuid, content_type FROM encrypted_object_tbl WHERE object_uuid = ?",
		objUUID,
	).Scan(&createdAfter, &updatedAfter, &schemaAfter, &contentAfter)
	if err != nil {
		t.Fatalf("failed to query post-update row: %v", err)
	}
	if createdAfter != createdBefore {
		t.Fatalf("created_at_ms must be preserved, before=%d after=%d", createdBefore, createdAfter)
	}
	if updatedAfter <= updatedBefore {
		t.Fatalf("updated_at_ms must advance, before=%d after=%d", updatedBefore, updatedAfter)
	}
	if schemaAfter != "00000000-0000-4000-8000-000000000002" {
		t.Fatalf("schema_uuid mismatch: %s", schemaAfter)
	}
	if contentAfter != "application/merge-patch+json" {
		t.Fatalf("content_type mismatch: %s", contentAfter)
	}

	reader, err := OpenReadOnly(dbPath, passphrase)
	if err != nil {
		t.Fatalf("OpenReadOnly failed: %v", err)
	}
	defer reader.Close()

	plaintext, err := reader.DecryptObject(objUUID)
	if err != nil {
		t.Fatalf("DecryptObject failed: %v", err)
	}
	if string(plaintext) != `{"hello":"world","v":2}` {
		t.Fatalf("updated payload mismatch: %s", string(plaintext))
	}
}

func TestWriterDeletePayloadOnlyDeletesObjectRow(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "vault_writer_delete_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "test.db")
	writer, err := CreateNew(dbPath, "test-passphrase", "linux")
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}
	defer writer.Close()

	objUUID, err := writer.StorePayload("00000000-0000-4000-8000-000000000001", "application/json", map[string]any{"x": 1})
	if err != nil {
		t.Fatalf("StorePayload failed: %v", err)
	}

	var keyBefore, wrappedBefore, unlockBefore int64
	if err := writer.db.QueryRow("SELECT COUNT(*) FROM key_tbl").Scan(&keyBefore); err != nil {
		t.Fatalf("count key_tbl failed: %v", err)
	}
	if err := writer.db.QueryRow("SELECT COUNT(*) FROM wrapped_key_tbl").Scan(&wrappedBefore); err != nil {
		t.Fatalf("count wrapped_key_tbl failed: %v", err)
	}
	if err := writer.db.QueryRow("SELECT COUNT(*) FROM unlock_kek_tbl").Scan(&unlockBefore); err != nil {
		t.Fatalf("count unlock_kek_tbl failed: %v", err)
	}

	if err := writer.DeletePayload(objUUID); err != nil {
		t.Fatalf("DeletePayload failed: %v", err)
	}

	var objectCount int64
	if err := writer.db.QueryRow("SELECT COUNT(*) FROM encrypted_object_tbl WHERE object_uuid = ?", objUUID).Scan(&objectCount); err != nil {
		t.Fatalf("count encrypted_object_tbl failed: %v", err)
	}
	if objectCount != 0 {
		t.Fatalf("expected deleted object row, remaining=%d", objectCount)
	}

	var keyAfter, wrappedAfter, unlockAfter int64
	_ = writer.db.QueryRow("SELECT COUNT(*) FROM key_tbl").Scan(&keyAfter)
	_ = writer.db.QueryRow("SELECT COUNT(*) FROM wrapped_key_tbl").Scan(&wrappedAfter)
	_ = writer.db.QueryRow("SELECT COUNT(*) FROM unlock_kek_tbl").Scan(&unlockAfter)
	if keyAfter != keyBefore || wrappedAfter != wrappedBefore || unlockAfter != unlockBefore {
		t.Fatalf("non-object tables changed: key %d->%d wrapped %d->%d unlock %d->%d", keyBefore, keyAfter, wrappedBefore, wrappedAfter, unlockBefore, unlockAfter)
	}
}

func TestWriterUpdateDeleteValidationAndNotFound(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "vault_writer_update_delete_negative_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	writer, err := CreateNew(filepath.Join(tempDir, "test.db"), "test-passphrase", "linux")
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}
	defer writer.Close()

	payload := map[string]any{"ok": true}

	if err := writer.UpdatePayload("invalid-uuid", "00000000-0000-4000-8000-000000000001", "application/json", payload); err == nil {
		t.Fatalf("expected invalid objectUUID error")
	}
	if err := writer.UpdatePayload("00000000-0000-4000-8000-000000000010", "invalid-uuid", "application/json", payload); err == nil {
		t.Fatalf("expected invalid schemaUUID error")
	}
	if err := writer.UpdatePayload("00000000-0000-4000-8000-000000000010", "00000000-0000-4000-8000-000000000001", "invalid", payload); err == nil {
		t.Fatalf("expected invalid content type error")
	}
	if err := writer.UpdatePayload("00000000-0000-4000-8000-000000000010", "00000000-0000-4000-8000-000000000001", "application/", payload); err == nil {
		t.Fatalf("expected invalid content type error for empty subtype")
	}
	if err := writer.UpdatePayload("00000000-0000-4000-8000-000000000010", "00000000-0000-4000-8000-000000000001", "application/\x07json", payload); err == nil {
		t.Fatalf("expected invalid content type error for control chars")
	}
	if err := writer.DeletePayload("invalid-uuid"); err == nil {
		t.Fatalf("expected invalid objectUUID error")
	}

	err = writer.UpdatePayload("00000000-0000-4000-8000-000000000010", "00000000-0000-4000-8000-000000000001", "application/json", payload)
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected ErrNotFound for missing update target, got: %v", err)
	}
	err = writer.DeletePayload("00000000-0000-4000-8000-000000000010")
	if !errors.Is(err, ErrNotFound) {
		t.Fatalf("expected ErrNotFound for missing delete target, got: %v", err)
	}

	// sanity: ensure no accidental object row was created
	var c int64
	rowErr := writer.db.QueryRow("SELECT COUNT(*) FROM encrypted_object_tbl").Scan(&c)
	if rowErr != nil && !errors.Is(rowErr, sql.ErrNoRows) {
		t.Fatalf("failed to count object rows: %v", rowErr)
	}
}
