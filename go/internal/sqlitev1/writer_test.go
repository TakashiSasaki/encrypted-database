package sqlitev1

import (
	"database/sql"
	"os"
	"path/filepath"
	"testing"
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


func TestCreateNewAppliesPragmas(t *testing.T) {
	tempDir, err := os.MkdirTemp("", "vault_writer_pragma_test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	dbPath := filepath.Join(tempDir, "test_pragma.db")
	writer, err := CreateNew(dbPath, "test-passphrase", "linux")
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}
	writer.Close()

	db, err := sql.Open("sqlite", dbPath)
	if err != nil {
		t.Fatalf("failed to open sqlite db: %v", err)
	}
	defer db.Close()

	var pageSize int
	if err := db.QueryRow("PRAGMA page_size").Scan(&pageSize); err != nil {
		t.Fatalf("failed to read PRAGMA page_size: %v", err)
	}
	if pageSize != 4096 {
		t.Fatalf("expected page_size=4096, got %d", pageSize)
	}

	var autoVacuum int
	if err := db.QueryRow("PRAGMA auto_vacuum").Scan(&autoVacuum); err != nil {
		t.Fatalf("failed to read PRAGMA auto_vacuum: %v", err)
	}
	if autoVacuum != 0 {
		t.Fatalf("expected auto_vacuum=0 (NONE), got %d", autoVacuum)
	}

	var journalMode string
	if err := db.QueryRow("PRAGMA journal_mode").Scan(&journalMode); err != nil {
		t.Fatalf("failed to read PRAGMA journal_mode: %v", err)
	}
	if journalMode != "wal" {
		t.Fatalf("expected journal_mode=wal, got %s", journalMode)
	}

	var synchronous int
	if err := db.QueryRow("PRAGMA synchronous").Scan(&synchronous); err != nil {
		t.Fatalf("failed to read PRAGMA synchronous: %v", err)
	}
	if synchronous != 1 && synchronous != 2 {
		t.Fatalf("expected synchronous NORMAL-equivalent (1 or 2), got %d", synchronous)
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
