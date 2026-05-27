package main

import (
	"encoding/json"
	"fmt"
	"os"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/sqlitev1"
)

func main() {
	if len(os.Args) < 8 {
		fmt.Fprintf(os.Stderr, "Usage: %s <mode> <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_json>\n", os.Args[0])
		os.Exit(1)
	}

	mode := os.Args[1]
	dbPath := os.Args[2]
	passphrase := os.Args[3]
	platform := os.Args[4]
	schemaUUID := os.Args[5]
	contentType := os.Args[6]
	payloadStr := os.Args[7]

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

	if mode == "update" {
		payloadStr2 := `{"secret": "matrix-test", "value": 100, "updated": true}`
		var payload2 interface{}
		json.Unmarshal([]byte(payloadStr2), &payload2)
		err = writer.UpdatePayload(objUUID, schemaUUID, contentType, payload2)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Failed to update payload: %v\n", err)
			os.Exit(1)
		}
		payload = payload2
	} else if mode == "delete" {
		err = writer.DeletePayload(objUUID)
		if err != nil {
			fmt.Fprintf(os.Stderr, "Failed to delete payload: %v\n", err)
			os.Exit(1)
		}
		fmt.Printf("%s\n%s\n", objUUID, "DELETED")
		return
	}

	expectedPayloadJCS, err := jcs.Canonicalize(payload)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to canonicalize payload: %v\n", err)
		os.Exit(1)
	}
	expectedPayloadHex := fmt.Sprintf("%x", expectedPayloadJCS)

	fmt.Printf("%s\n%s\n", objUUID, expectedPayloadHex)
}
