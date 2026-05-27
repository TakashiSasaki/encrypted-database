package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/sqlitev1"
)

func main() {
	if len(os.Args) < 7 {
		fmt.Fprintf(os.Stderr, "Usage: %s <db_path> <passphrase> <object_uuid> <schema_uuid> <content_type> <payload_json>\n", os.Args[0])
		os.Exit(1)
	}

	dbPath := os.Args[1]
	passphrase := os.Args[2]
	objectUUID := os.Args[3]
	schemaUUID := os.Args[4]
	contentType := os.Args[5]
	payloadStr := os.Args[6]

	var payload interface{}
	if err := json.Unmarshal([]byte(payloadStr), &payload); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to parse payload JSON: %v\n", err)
		os.Exit(1)
	}

	writer, err := sqlitev1.OpenWriter(dbPath, passphrase)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to open DB: %v\n", err)
		os.Exit(1)
	}
	defer writer.Close()

	if err := writer.UpdatePayload(objectUUID, schemaUUID, contentType, payload); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to update payload: %v\n", err)
		os.Exit(1)
	}
}
