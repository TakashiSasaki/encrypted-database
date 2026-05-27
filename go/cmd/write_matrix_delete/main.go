package main

import (
	"fmt"
	"os"

	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/sqlitev1"
)

func main() {
	if len(os.Args) < 4 {
		fmt.Fprintf(os.Stderr, "Usage: %s <db_path> <passphrase> <object_uuid>\n", os.Args[0])
		os.Exit(1)
	}

	dbPath := os.Args[1]
	passphrase := os.Args[2]
	objectUUID := os.Args[3]

	writer, err := sqlitev1.OpenWriter(dbPath, passphrase)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Failed to open DB: %v\n", err)
		os.Exit(1)
	}
	defer writer.Close()

	if err := writer.DeletePayload(objectUUID); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to delete payload: %v\n", err)
		os.Exit(1)
	}
}
