package sqlitev1

import (
	"os"
	"path/filepath"
	"testing"
)

func TestWriterUpdateDelete(t *testing.T) {
	tempDir := t.TempDir()
	dbPath := filepath.Join(tempDir, "test.db")
	passphrase := "test-passphrase"
	platform := "linux"
	schemaUUID := "00000000-0000-4000-8000-000000000001"
	contentType := "application/json"
	payload1 := map[string]interface{}{"val": 1}
	payload2 := map[string]interface{}{"val": 2}

	os.Setenv("VAULT_SCHEMA_SQL_PATH", "../../../docs/backend/sqlite/schema.sql")

	writer, err := CreateNew(dbPath, passphrase, platform)
	if err != nil {
		t.Fatalf("CreateNew failed: %v", err)
	}

	objUUID, err := writer.StorePayload(schemaUUID, contentType, payload1)
	if err != nil {
		t.Fatalf("StorePayload failed: %v", err)
	}

	err = writer.UpdatePayload(objUUID, schemaUUID, contentType, payload2)
	if err != nil {
		t.Fatalf("UpdatePayload failed: %v", err)
	}

	err = writer.DeletePayload(objUUID)
	if err != nil {
		t.Fatalf("DeletePayload failed: %v", err)
	}

	err = writer.DeletePayload(objUUID)
	if err == nil {
		t.Fatalf("Expected error on second DeletePayload, got nil")
	}

	err = writer.UpdatePayload(objUUID, schemaUUID, contentType, payload2)
	if err == nil {
		t.Fatalf("Expected error on UpdatePayload after delete, got nil")
	}

	writer.Close()
}
