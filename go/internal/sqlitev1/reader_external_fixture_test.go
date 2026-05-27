package sqlitev1

import (
	"encoding/hex"
	"errors"
	"os"
	"testing"
)

func TestExternalFixtureReadOnly(t *testing.T) {
	dbPath := os.Getenv("VAULT_SQLITE_V1_FIXTURE_DB")
	passphrase := os.Getenv("VAULT_SQLITE_V1_FIXTURE_PASSPHRASE")
	objectUUID := os.Getenv("VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID")
	expectedPayloadHex := os.Getenv("VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX")
	expectNotFound := os.Getenv("VAULT_SQLITE_V1_FIXTURE_EXPECT_NOT_FOUND") == "1"

	if dbPath == "" || passphrase == "" || objectUUID == "" || (!expectNotFound && expectedPayloadHex == "") {
		t.Skip("External fixture integration test skipped: missing VAULT_SQLITE_V1_FIXTURE_* environment variables")
	}

	reader, err := OpenReadOnly(dbPath, passphrase)
	if err != nil {
		t.Fatalf("Failed to open external fixture DB: %v", err)
	}
	defer reader.Close()

	payloadBytes, err := reader.DecryptObject(objectUUID)
	if expectNotFound {
		if err == nil || !errors.Is(err, ErrNotFound) {
			t.Fatalf("Expected ErrNotFound for object %s, got: %v", objectUUID, err)
		}
		return
	}
	if err != nil {
		t.Fatalf("Failed to decrypt object %s: %v", objectUUID, err)
	}

	actualPayloadHex := hex.EncodeToString(payloadBytes)
	if actualPayloadHex != expectedPayloadHex {
		t.Errorf("Decrypted payload hex mismatch.\nExpected: %s\nActual:   %s", expectedPayloadHex, actualPayloadHex)
	}
}
