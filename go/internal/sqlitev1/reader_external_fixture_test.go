package sqlitev1

import (
	"encoding/hex"
	"os"
	"testing"
)

func TestExternalFixtureReadOnly(t *testing.T) {
	dbPath := os.Getenv("VAULT_SQLITE_V1_FIXTURE_DB")
	passphrase := os.Getenv("VAULT_SQLITE_V1_FIXTURE_PASSPHRASE")
	objectUUID := os.Getenv("VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID")
	expectedPayloadHex := os.Getenv("VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX")

	if dbPath == "" || passphrase == "" || objectUUID == "" || expectedPayloadHex == "" {
		t.Skip("External fixture integration test skipped: missing VAULT_SQLITE_V1_FIXTURE_* environment variables")
	}

	reader, err := OpenReadOnly(dbPath, passphrase)
	if err != nil {
		t.Fatalf("Failed to open external fixture DB: %v", err)
	}
	defer reader.Close()

	payloadBytes, err := reader.DecryptObject(objectUUID)
	if err != nil {
		t.Fatalf("Failed to decrypt object %s: %v", objectUUID, err)
	}

	actualPayloadHex := hex.EncodeToString(payloadBytes)
	if actualPayloadHex != expectedPayloadHex {
		t.Errorf("Decrypted payload hex mismatch.\nExpected: %s\nActual:   %s", expectedPayloadHex, actualPayloadHex)
	}
}
