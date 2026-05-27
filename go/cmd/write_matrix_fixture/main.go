package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/sqlitev1"
)

func main() {
	if len(os.Args) < 7 {
		fmt.Fprintf(os.Stderr, "Usage: %s <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_json>\n", os.Args[0])
		os.Exit(1)
	}

	dbPath := os.Args[1]
	passphrase := os.Args[2]
	platform := os.Args[3]
	schemaUUID := os.Args[4]
	contentType := os.Args[5]
	payloadStr := os.Args[6]

	var payload interface{}
	if err := json.Unmarshal([]byte(payloadStr), &payload); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to parse payload JSON: %v\n", err)
		os.Exit(1)
	}

	writer, err := sqlitev1.CreateNew(dbPath, passphrase, platform)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to create DB: %v\n", err)
		os.Exit(1)
	}
	defer writer.Close()

	objUUID, err := writer.StorePayload(schemaUUID, contentType, payload)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to store payload: %v\n", err)
		os.Exit(1)
	}

	expectedPayloadJCS, err := jcs.Canonicalize(payload)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to canonicalize payload: %v\n", err)
		os.Exit(1)
	}
	expectedPayloadHex := fmt.Sprintf("%x", expectedPayloadJCS)

	fmt.Printf("%s\n%s\n", objUUID, expectedPayloadHex)
}
