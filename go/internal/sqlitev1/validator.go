package sqlitev1

import (
	"database/sql"
	"errors"
	"fmt"
	"net/url"
	"regexp"
	"strings"

	_ "modernc.org/sqlite"
)

var (
	// uuidRegex enforces strict UUID shape: lowercase canonical text with accepted version (1-8) and RFC4122/RFC9562-compatible variant (8,9,a,b).
	uuidRegex      = regexp.MustCompile(`^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$`)
	timestampRegex = regexp.MustCompile(`^(0|[1-9][0-9]*)$`)
)

type ValidationResult struct {
	DatabaseUUID string
}

func ValidateReadOnly(path string) (*ValidationResult, error) {
	// Connect strictly read-only
	// Properly escape path for SQLite URI to avoid injection or breaking on '#' / '?'
	parsedURL := &url.URL{
		Scheme: "file",
		Opaque: url.PathEscape(path),
	}
	q := parsedURL.Query()
	q.Set("mode", "ro")
	parsedURL.RawQuery = q.Encode()

	db, err := sql.Open("sqlite", parsedURL.String())
	if err != nil {
		return nil, fmt.Errorf("failed to open database: %w", err)
	}
	defer db.Close()

	// 1. Read PRAGMA application_id
	var appId int64
	err = db.QueryRow("PRAGMA application_id").Scan(&appId)
	if err != nil {
		return nil, fmt.Errorf("failed to read PRAGMA application_id: %w", err)
	}
	if appId != 1447906135 {
		return nil, fmt.Errorf("invalid PRAGMA application_id: %d", appId)
	}

	// 2. Read PRAGMA user_version
	var userVersion int64
	err = db.QueryRow("PRAGMA user_version").Scan(&userVersion)
	if err != nil {
		return nil, fmt.Errorf("failed to read PRAGMA user_version: %w", err)
	}
	if userVersion != 1 {
		return nil, fmt.Errorf("invalid PRAGMA user_version: %d", userVersion)
	}

	// 3. Ensure storage_metadata_tbl exists and fetch all properties
	// In SQLite, checking if table exists:
	var tableName string
	err = db.QueryRow("SELECT name FROM sqlite_master WHERE type='table' AND name='storage_metadata_tbl'").Scan(&tableName)
	if err != nil {
		if errors.Is(err, sql.ErrNoRows) {
			return nil, errors.New("missing storage_metadata_tbl")
		}
		return nil, fmt.Errorf("failed to query storage_metadata_tbl existence: %w", err)
	}

	rows, err := db.Query("SELECT property, value FROM storage_metadata_tbl")
	if err != nil {
		return nil, fmt.Errorf("failed to query storage_metadata_tbl: %w", err)
	}
	defer rows.Close()

	metadata := make(map[string]string)
	for rows.Next() {
		var prop, val string
		if err := rows.Scan(&prop, &val); err != nil {
			return nil, fmt.Errorf("failed to scan metadata row: %w", err)
		}
		metadata[prop] = val
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("metadata rows error: %w", err)
	}

	// 4. Validate metadata fields
	if val, ok := metadata["storage_format_id"]; !ok || val != "vault.moukaeritai.work.storage" {
		return nil, fmt.Errorf("invalid storage_format_id: %v", metadata["storage_format_id"])
	}
	if val, ok := metadata["format_major"]; !ok || val != "1" {
		return nil, fmt.Errorf("invalid format_major: %v", metadata["format_major"])
	}
	if val, ok := metadata["format_minor"]; !ok || val != "0" {
		return nil, fmt.Errorf("invalid format_minor: %v", metadata["format_minor"])
	}
	if val, ok := metadata["schema_version"]; !ok || val != "1" {
		return nil, fmt.Errorf("invalid schema_version: %v", metadata["schema_version"])
	}
	if val, ok := metadata["required_features"]; !ok || val != "[]" {
		return nil, fmt.Errorf("invalid required_features: %v", metadata["required_features"])
	}
	if val, ok := metadata["optional_features"]; !ok || val != "[]" {
		return nil, fmt.Errorf("invalid optional_features: %v", metadata["optional_features"])
	}

	dbUuid, ok := metadata["database_uuid"]
	if !ok || !uuidRegex.MatchString(dbUuid) {
		return nil, fmt.Errorf("invalid database_uuid: %v", metadata["database_uuid"])
	}

	createdAt, ok := metadata["created_at_ms"]
	if !ok || !timestampRegex.MatchString(createdAt) {
		return nil, fmt.Errorf("invalid created_at_ms: %v", metadata["created_at_ms"])
	}

	createdByLib, ok := metadata["created_by_library"]
	if !ok || strings.TrimSpace(createdByLib) == "" {
		return nil, fmt.Errorf("invalid created_by_library")
	}
	createdByVer, ok := metadata["created_by_version"]
	if !ok || strings.TrimSpace(createdByVer) == "" {
		return nil, fmt.Errorf("invalid created_by_version")
	}

	// PRAGMA matches against metadata
	if val, ok := metadata["sqlite_application_id"]; !ok || val != "1447906135" {
		return nil, fmt.Errorf("invalid or missing metadata sqlite_application_id: %v", val)
	}
	if val, ok := metadata["sqlite_user_version"]; !ok || val != "1" {
		return nil, fmt.Errorf("invalid or missing metadata sqlite_user_version: %v", val)
	}

	return &ValidationResult{
		DatabaseUUID: dbUuid,
	}, nil
}
