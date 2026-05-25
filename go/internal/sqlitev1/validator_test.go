package sqlitev1_test

import (
	"database/sql"
	"path/filepath"
	"testing"
	"time"

	"fmt"
	"github.com/TakashiSasaki/vault.moukaeritai.work/go/internal/sqlitev1"
	_ "modernc.org/sqlite"
)

func createValidDb(t *testing.T, path string) {
	db, err := sql.Open("sqlite", path)
	if err != nil {
		t.Fatalf("failed to create db: %v", err)
	}
	defer db.Close()

	_, err = db.Exec("PRAGMA application_id = 1447906135")
	if err != nil {
		t.Fatalf("failed to set application_id: %v", err)
	}

	_, err = db.Exec("PRAGMA user_version = 1")
	if err != nil {
		t.Fatalf("failed to set user_version: %v", err)
	}

	_, err = db.Exec(`
		CREATE TABLE storage_metadata_tbl (
			property TEXT PRIMARY KEY,
			value TEXT NOT NULL
		)
	`)
	if err != nil {
		t.Fatalf("failed to create table: %v", err)
	}

	insertMetadata := `INSERT INTO storage_metadata_tbl (property, value) VALUES (?, ?)`
	metadata := map[string]string{
		"storage_format_id":     "vault.moukaeritai.work.storage",
		"format_major":          "1",
		"format_minor":          "0",
		"schema_version":        "1",
		"database_uuid":         "12345678-1234-4234-8234-123456789abc",
		"created_at_ms":         "1600000000000",
		"created_by_library":    "test",
		"created_by_version":    "1.0",
		"required_features":     "[]",
		"optional_features":     "[]",
		"sqlite_application_id": "1447906135",
		"sqlite_user_version":   "1",
	}

	for k, v := range metadata {
		if _, err := db.Exec(insertMetadata, k, v); err != nil {
			t.Fatalf("failed to insert metadata %s: %v", k, err)
		}
	}
}

func TestValidateReadOnly_Valid(t *testing.T) {
	tmpDir := t.TempDir()

	validUUIDs := []string{
		"12345678-1234-4234-8234-123456789abc", // version 4, variant 8
		"12345678-1234-7234-9234-123456789abc", // version 7, variant 9
		"12345678-1234-8234-a234-123456789abc", // version 8, variant a
		"12345678-1234-1234-b234-123456789abc", // version 1, variant b
	}

	for i, uuid := range validUUIDs {
		t.Run(fmt.Sprintf("valid_%d", i), func(t *testing.T) {
			dbPath := filepath.Join(tmpDir, fmt.Sprintf("valid_%d.db", i))
			createValidDb(t, dbPath)

			// Update to a specific valid UUID
			db, err := sql.Open("sqlite", dbPath)
			if err != nil {
				t.Fatalf("setup open: %v", err)
			}
			if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'database_uuid'", uuid); err != nil {
				t.Fatalf("setup exec: %v", err)
			}
			db.Close()

			res, err := sqlitev1.ValidateReadOnly(dbPath)
			if err != nil {
				t.Fatalf("expected valid db to pass with UUID %s, got: %v", uuid, err)
			}
			if res.DatabaseUUID != uuid {
				t.Errorf("unexpected database_uuid: got %s, want %s", res.DatabaseUUID, uuid)
			}
		})
	}
}

func TestValidateReadOnly_InvalidCases(t *testing.T) {
	cases := []struct {
		name     string
		setup    func(*testing.T, string)
		errCheck string
	}{
		{
			name: "missing storage_metadata_tbl",
			setup: func(t *testing.T, path string) {
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("PRAGMA application_id = 1447906135"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
				if _, err := db.Exec("PRAGMA user_version = 1"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "missing storage_metadata_tbl",
		},
		{
			name: "wrong PRAGMA application_id",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("PRAGMA application_id = 12345"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid PRAGMA application_id",
		},
		{
			name: "wrong storage_format_id",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = 'wrong' WHERE property = 'storage_format_id'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid storage_format_id",
		},
		{
			name: "missing format_major",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("DELETE FROM storage_metadata_tbl WHERE property = 'format_major'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid format_major",
		},
		{
			name: "invalid format_minor = 1",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '1' WHERE property = 'format_minor'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid format_minor",
		},
		{
			name: "wrong format_major",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '2' WHERE property = 'format_major'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid format_major",
		},
		{
			name: "invalid database_uuid",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = 'invalid-uuid' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid database_uuid uppercase",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '12345678-1234-4234-8234-123456789ABC' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid database_uuid leading whitespace",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = ' 12345678-1234-4234-8234-123456789abc' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid database_uuid trailing whitespace",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '12345678-1234-4234-8234-123456789abc ' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid database_uuid version 0",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '12345678-1234-0234-8234-123456789abc' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid database_uuid version 9",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '12345678-1234-9234-8234-123456789abc' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid database_uuid variant 7",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '12345678-1234-4234-7234-123456789abc' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid database_uuid variant c",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '12345678-1234-4234-c234-123456789abc' WHERE property = 'database_uuid'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid database_uuid",
		},
		{
			name: "invalid created_at_ms",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = 'not-a-number' WHERE property = 'created_at_ms'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid created_at_ms",
		},
		{
			name: "invalid created_at_ms negative",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '-1' WHERE property = 'created_at_ms'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid created_at_ms",
		},
		{
			name: "invalid created_at_ms plus sign",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '+1' WHERE property = 'created_at_ms'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid created_at_ms",
		},
		{
			name: "invalid created_at_ms float",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '1.0' WHERE property = 'created_at_ms'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid created_at_ms",
		},
		{
			name: "invalid created_at_ms whitespace",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = ' 123' WHERE property = 'created_at_ms'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid created_at_ms",
		},
		{
			name: "non-empty required_features",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '[\"something\"]' WHERE property = 'required_features'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid required_features",
		},
		{
			name: "invalid required_features spacing",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '[ ]' WHERE property = 'required_features'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid required_features",
		},
		{
			name: "invalid optional_features spacing",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '[ ]' WHERE property = 'optional_features'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid optional_features",
		},
		{
			name: "non-empty optional_features",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '[\"x\"]' WHERE property = 'optional_features'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid optional_features",
		},
		{
			name: "invalid created_by_library whitespace-only",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '   ' WHERE property = 'created_by_library'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid created_by_library",
		},
		{
			name: "invalid created_by_version whitespace-only",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '\t' WHERE property = 'created_by_version'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid created_by_version",
		},
		{
			name: "missing sqlite_application_id metadata",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("DELETE FROM storage_metadata_tbl WHERE property = 'sqlite_application_id'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid or missing metadata sqlite_application_id",
		},
		{
			name: "missing sqlite_user_version metadata",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("DELETE FROM storage_metadata_tbl WHERE property = 'sqlite_user_version'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid or missing metadata sqlite_user_version",
		},
		{
			name: "PRAGMA mismatch sqlite_application_id",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '123' WHERE property = 'sqlite_application_id'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid or missing metadata sqlite_application_id",
		},
		{
			name: "PRAGMA mismatch sqlite_user_version",
			setup: func(t *testing.T, path string) {
				createValidDb(t, path)
				db, err := sql.Open("sqlite", path)
				if err != nil {
					t.Fatalf("setup open: %v", err)
				}
				defer db.Close()
				if _, err := db.Exec("UPDATE storage_metadata_tbl SET value = '123' WHERE property = 'sqlite_user_version'"); err != nil {
					t.Fatalf("setup exec: %v", err)
				}
			},
			errCheck: "invalid or missing metadata sqlite_user_version",
		},
	}

	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			tmpDir := t.TempDir()
			dbPath := filepath.Join(tmpDir, "invalid.db")
			tc.setup(t, dbPath)

			// Introduce a small sleep to ensure db file locks are released from setup
			time.Sleep(10 * time.Millisecond)

			_, err := sqlitev1.ValidateReadOnly(dbPath)
			if err == nil {
				t.Fatalf("expected error containing %q, got nil", tc.errCheck)
			}
		})
	}
}
