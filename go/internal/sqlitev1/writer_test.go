package sqlitev1

import (
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
