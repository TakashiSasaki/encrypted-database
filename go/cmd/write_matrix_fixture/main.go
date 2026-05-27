package main

import (
	"encoding/hex"
	"encoding/json"
	"fmt"
	"os"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/jcs"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/sqlitev1"
)

type fixtureOutput struct {
	ObjectUUID        string `json:"object_uuid"`
	InitialPayloadHex string `json:"initial_payload_hex"`
	UpdatedPayloadHex string `json:"updated_payload_hex"`
	Deleted           bool   `json:"deleted"`
}

func main() {
	if len(os.Args) < 8 {
		fmt.Fprintf(os.Stderr, "Usage: %s <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a_json> <payload_b_json> [mode:update_only|update_delete]\n", os.Args[0])
		os.Exit(1)
	}

	dbPath, passphrase, platform, schemaUUID, contentType := os.Args[1], os.Args[2], os.Args[3], os.Args[4], os.Args[5]
	payloadAStr, payloadBStr := os.Args[6], os.Args[7]
	mode := "update_delete"
	if len(os.Args) >= 9 {
		mode = os.Args[8]
	}
	if mode != "update_only" && mode != "update_delete" {
		fmt.Fprintf(os.Stderr, "invalid mode: %s\n", mode)
		os.Exit(1)
	}

	var payloadA, payloadB interface{}
	if err := json.Unmarshal([]byte(payloadAStr), &payloadA); err != nil {
		fmt.Fprintf(os.Stderr, "payload A parse error: %v\n", err)
		os.Exit(1)
	}
	if err := json.Unmarshal([]byte(payloadBStr), &payloadB); err != nil {
		fmt.Fprintf(os.Stderr, "payload B parse error: %v\n", err)
		os.Exit(1)
	}

	writer, err := sqlitev1.CreateNew(dbPath, passphrase, platform)
	if err != nil {
		fmt.Fprintf(os.Stderr, "create DB error: %v\n", err)
		os.Exit(1)
	}
	defer writer.Close()

	objUUID, err := writer.StorePayload(schemaUUID, contentType, payloadA)
	if err != nil {
		fmt.Fprintf(os.Stderr, "store error: %v\n", err)
		os.Exit(1)
	}
	if err := writer.UpdatePayload(objUUID, schemaUUID, contentType, payloadB); err != nil {
		fmt.Fprintf(os.Stderr, "update error: %v\n", err)
		os.Exit(1)
	}

	deleted := false
	if mode == "update_delete" {
		if err := writer.DeletePayload(objUUID); err != nil {
			fmt.Fprintf(os.Stderr, "delete error: %v\n", err)
			os.Exit(1)
		}
		deleted = true
	}

	initialJCS, err := jcs.Canonicalize(payloadA)
	if err != nil {
		fmt.Fprintf(os.Stderr, "canonicalize A error: %v\n", err)
		os.Exit(1)
	}
	updatedJCS, err := jcs.Canonicalize(payloadB)
	if err != nil {
		fmt.Fprintf(os.Stderr, "canonicalize B error: %v\n", err)
		os.Exit(1)
	}
	out := fixtureOutput{objUUID, hex.EncodeToString([]byte(initialJCS)), hex.EncodeToString([]byte(updatedJCS)), deleted}
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	if err := enc.Encode(out); err != nil {
		fmt.Fprintf(os.Stderr, "output encode error: %v\n", err)
		os.Exit(1)
	}
}
