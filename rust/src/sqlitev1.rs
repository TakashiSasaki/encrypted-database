use regex::Regex;
use rusqlite::{Connection, OpenFlags};
use std::collections::HashMap;
use std::path::Path;
use std::sync::OnceLock;
use thiserror::Error;

#[derive(Debug, Error)]
pub enum SqliteV1Error {
    #[error("Failed to open database: {0}")]
    OpenError(#[from] rusqlite::Error),
    #[error("Missing storage_metadata_tbl")]
    MissingMetadataTable,
    #[error("Invalid PRAGMA application_id: {0}")]
    InvalidApplicationId(i64),
    #[error("Invalid PRAGMA user_version: {0}")]
    InvalidUserVersion(i64),
    #[error("Invalid property in metadata: {0}")]
    InvalidMetadataProperty(String),
    #[error("Missing property in metadata: {0}")]
    MissingMetadataProperty(String),
}

#[derive(Debug)]
pub struct ValidationResult {
    pub database_uuid: String,
}

static UUID_REGEX: OnceLock<Regex> = OnceLock::new();
static TIMESTAMP_REGEX: OnceLock<Regex> = OnceLock::new();

fn uuid_regex() -> &'static Regex {
    UUID_REGEX.get_or_init(|| {
        Regex::new(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$").unwrap()
    })
}

fn timestamp_regex() -> &'static Regex {
    TIMESTAMP_REGEX.get_or_init(|| Regex::new(r"^(0|[1-9][0-9]*)$").unwrap())
}

pub fn validate_read_only(path: &Path) -> Result<ValidationResult, SqliteV1Error> {
    let conn = Connection::open_with_flags(
        path,
        OpenFlags::SQLITE_OPEN_READ_ONLY | OpenFlags::SQLITE_OPEN_URI,
    )?;

    // 1. Read PRAGMA application_id
    let mut stmt = conn.prepare("PRAGMA application_id")?;
    let app_id: i64 = stmt.query_row([], |row| row.get(0))?;
    if app_id != 1447906135 {
        return Err(SqliteV1Error::InvalidApplicationId(app_id));
    }

    // 2. Read PRAGMA user_version
    let mut stmt = conn.prepare("PRAGMA user_version")?;
    let user_version: i64 = stmt.query_row([], |row| row.get(0))?;
    if user_version != 1 {
        return Err(SqliteV1Error::InvalidUserVersion(user_version));
    }

    // 3. Check storage_metadata_tbl existence
    let mut stmt = conn.prepare(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='storage_metadata_tbl'",
    )?;
    let exists: Option<String> = stmt.query_row([], |row| row.get(0)).ok();
    if exists.is_none() {
        return Err(SqliteV1Error::MissingMetadataTable);
    }

    // 4. Read metadata table
    let mut stmt = conn.prepare("SELECT property, value FROM storage_metadata_tbl")?;
    let rows = stmt.query_map([], |row| {
        let prop: String = row.get(0)?;
        let val: String = row.get(1)?;
        Ok((prop, val))
    })?;

    let mut metadata = HashMap::new();
    for row in rows {
        let (prop, val) = row?;
        metadata.insert(prop, val);
    }

    // Helper closure to get required property
    let get_req = |key: &str| -> Result<&String, SqliteV1Error> {
        metadata
            .get(key)
            .ok_or_else(|| SqliteV1Error::MissingMetadataProperty(key.to_string()))
    };

    if get_req("storage_format_id")? != "vault.moukaeritai.work.storage" {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "storage_format_id".into(),
        ));
    }
    if get_req("format_major")? != "1" {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "format_major".into(),
        ));
    }
    if get_req("format_minor")? != "0" {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "format_minor".into(),
        ));
    }
    if get_req("schema_version")? != "1" {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "schema_version".into(),
        ));
    }
    if get_req("required_features")? != "[]" {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "required_features".into(),
        ));
    }
    if get_req("optional_features")? != "[]" {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "optional_features".into(),
        ));
    }

    let db_uuid = get_req("database_uuid")?;
    if !uuid_regex().is_match(db_uuid) {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "database_uuid".into(),
        ));
    }

    let created_at = get_req("created_at_ms")?;
    if !timestamp_regex().is_match(created_at) {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "created_at_ms".into(),
        ));
    }

    if get_req("created_by_library")?.trim().is_empty() {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "created_by_library".into(),
        ));
    }
    if get_req("created_by_version")?.trim().is_empty() {
        return Err(SqliteV1Error::InvalidMetadataProperty(
            "created_by_version".into(),
        ));
    }

    if let Some(sqlite_app_id) = metadata.get("sqlite_application_id") {
        if sqlite_app_id != "1447906135" {
            return Err(SqliteV1Error::InvalidMetadataProperty(
                "sqlite_application_id".into(),
            ));
        }
    }
    if let Some(sqlite_user_ver) = metadata.get("sqlite_user_version") {
        if sqlite_user_ver != "1" {
            return Err(SqliteV1Error::InvalidMetadataProperty(
                "sqlite_user_version".into(),
            ));
        }
    }

    Ok(ValidationResult {
        database_uuid: db_uuid.clone(),
    })
}
