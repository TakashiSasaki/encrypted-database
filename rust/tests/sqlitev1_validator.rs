use rusqlite::Connection;
use std::path::PathBuf;
use tempfile::tempdir;
use vault_moukaeritai_work::sqlitev1::validate_read_only;

fn create_valid_db(path: &PathBuf) {
    let conn = Connection::open(path).unwrap();

    conn.execute("PRAGMA application_id = 1447906135", [])
        .unwrap();
    conn.execute("PRAGMA user_version = 1", []).unwrap();
    conn.execute(
        "CREATE TABLE storage_metadata_tbl (
            property TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )",
        [],
    )
    .unwrap();

    let metadata = vec![
        ("storage_format_id", "vault.moukaeritai.work.storage"),
        ("format_major", "1"),
        ("format_minor", "0"),
        ("schema_version", "1"),
        ("database_uuid", "12345678-1234-4234-8234-123456789abc"),
        ("created_at_ms", "1600000000000"),
        ("created_by_library", "test"),
        ("created_by_version", "1.0"),
        ("required_features", "[]"),
        ("optional_features", "[]"),
        ("sqlite_application_id", "1447906135"),
        ("sqlite_user_version", "1"),
    ];

    for (k, v) in metadata {
        conn.execute(
            "INSERT INTO storage_metadata_tbl (property, value) VALUES (?1, ?2)",
            [k, v],
        )
        .unwrap();
    }
}

#[test]
fn test_validate_read_only_valid() {
    let dir = tempdir().unwrap();
    let db_path = dir.path().join("valid.db");
    create_valid_db(&db_path);

    let res = validate_read_only(&db_path).expect("expected valid db to pass");
    assert_eq!(res.database_uuid, "12345678-1234-4234-8234-123456789abc");
}

#[test]
fn test_validate_read_only_invalid_cases() {
    let cases: Vec<(&str, fn(&PathBuf), &str)> = vec![
        (
            "missing storage_metadata_tbl",
            |path: &PathBuf| {
                let conn = Connection::open(path).unwrap();
                conn.execute("PRAGMA application_id = 1447906135", [])
                    .unwrap();
                conn.execute("PRAGMA user_version = 1", []).unwrap();
            },
            "Missing storage_metadata_tbl",
        ),
        (
            "wrong PRAGMA application_id",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute("PRAGMA application_id = 12345", []).unwrap();
            },
            "Invalid PRAGMA application_id",
        ),
        (
            "wrong storage_format_id",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute("UPDATE storage_metadata_tbl SET value = 'wrong' WHERE property = 'storage_format_id'", []).unwrap();
            },
            "Invalid property in metadata: storage_format_id",
        ),
        (
            "missing format_major",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute(
                    "DELETE FROM storage_metadata_tbl WHERE property = 'format_major'",
                    [],
                )
                .unwrap();
            },
            "Missing property in metadata: format_major",
        ),
        (
            "invalid database_uuid",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute("UPDATE storage_metadata_tbl SET value = 'invalid-uuid' WHERE property = 'database_uuid'", []).unwrap();
            },
            "Invalid property in metadata: database_uuid",
        ),
        (
            "invalid created_at_ms",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute("UPDATE storage_metadata_tbl SET value = 'not-a-number' WHERE property = 'created_at_ms'", []).unwrap();
            },
            "Invalid property in metadata: created_at_ms",
        ),
        (
            "non-empty required_features",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute("UPDATE storage_metadata_tbl SET value = '[\"something\"]' WHERE property = 'required_features'", []).unwrap();
            },
            "Invalid property in metadata: required_features",
        ),
        (
            "missing sqlite_application_id metadata",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute(
                    "DELETE FROM storage_metadata_tbl WHERE property = 'sqlite_application_id'",
                    [],
                )
                .unwrap();
            },
            "Missing property in metadata: sqlite_application_id",
        ),
        (
            "missing sqlite_user_version metadata",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute(
                    "DELETE FROM storage_metadata_tbl WHERE property = 'sqlite_user_version'",
                    [],
                )
                .unwrap();
            },
            "Missing property in metadata: sqlite_user_version",
        ),
        (
            "PRAGMA mismatch",
            |path: &PathBuf| {
                create_valid_db(path);
                let conn = Connection::open(path).unwrap();
                conn.execute("UPDATE storage_metadata_tbl SET value = '123' WHERE property = 'sqlite_application_id'", []).unwrap();
            },
            "Invalid property in metadata: sqlite_application_id",
        ),
    ];

    for (name, setup, err_msg) in cases {
        let dir = tempdir().unwrap();
        let db_path = dir.path().join("invalid.db");
        setup(&db_path);

        let err = validate_read_only(&db_path).unwrap_err();
        assert!(
            err.to_string().contains(err_msg),
            "Test '{}' failed: expected error containing '{}', got '{}'",
            name,
            err_msg,
            err
        );
    }
}
