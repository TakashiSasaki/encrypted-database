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
		fmt.Fprintf(os.Stderr, "Usage: %s <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a_json> <payload_b_json>\n", os.Args[0])
		os.Exit(1)
	}

	dbPath, passphrase, platform, schemaUUID, contentType := os.Args[1], os.Args[2], os.Args[3], os.Args[4], os.Args[5]
	payloadAStr, payloadBStr := os.Args[6], os.Args[7]

	var payloadA, payloadB interface{}
	if err := json.Unmarshal([]byte(payloadAStr), &payloadA); err != nil {
		panic(err)
	}
	if err := json.Unmarshal([]byte(payloadBStr), &payloadB); err != nil {
		panic(err)
	}

	writer, err := sqlitev1.CreateNew(dbPath, passphrase, platform)
	if err != nil {
		panic(err)
	}
	defer writer.Close()

	objUUID, err := writer.StorePayload(schemaUUID, contentType, payloadA)
	if err != nil {
		panic(err)
	}
	if err := writer.UpdatePayload(objUUID, schemaUUID, contentType, payloadB); err != nil {
		panic(err)
	}
	if err := writer.DeletePayload(objUUID); err != nil {
		panic(err)
	}

	initialJCS, _ := jcs.Canonicalize(payloadA)
	updatedJCS, _ := jcs.Canonicalize(payloadB)
	out := fixtureOutput{objUUID, hex.EncodeToString([]byte(initialJCS)), hex.EncodeToString([]byte(updatedJCS)), true}
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	_ = enc.Encode(out)
}
