const std = @import("std");

pub fn smokeMessage() []const u8 {
    return "vault zig smoke test ok";
}

test "smokeMessage returns expected string" {
    try std.testing.expectEqualStrings("vault zig smoke test ok", smokeMessage());
}

test "sqlite wrapper basic" {
    _ = @import("sqlite.zig");
    const c = @cImport({
        @cInclude("sqlite3.h");
    });
    var db: ?*c.sqlite3 = null;
    const rc = c.sqlite3_open_v2(":memory:", &db, c.SQLITE_OPEN_READWRITE | c.SQLITE_OPEN_MEMORY, null);
    try std.testing.expectEqual(c.SQLITE_OK, rc);
    _ = c.sqlite3_close(db);
}

test "uuid validation" {
    const uuid = @import("uuid.zig");
    // valid
    try uuid.validateCanonical("00000000-0000-4000-8000-000000000001");
    try uuid.validateCanonical("12345678-abcd-1ef0-8123-456789abcdef");
    try uuid.validateCanonical("12345678-abcd-8ef0-9123-456789abcdef");
    try uuid.validateCanonical("12345678-abcd-8ef0-a123-456789abcdef");
    try uuid.validateCanonical("12345678-abcd-8ef0-b123-456789abcdef");

    // invalid
    try std.testing.expectError(uuid.UuidError.InvalidLength, uuid.validateCanonical("12345678-abcd-4ef0-8123-456789abcde")); // short
    try std.testing.expectError(uuid.UuidError.InvalidHyphen, uuid.validateCanonical("12345678_abcd-4ef0-8123-456789abcdef")); // bad hyphen
    try std.testing.expectError(uuid.UuidError.InvalidVersion, uuid.validateCanonical("12345678-abcd-9ef0-8123-456789abcdef")); // bad version (9)
    try std.testing.expectError(uuid.UuidError.InvalidVariant, uuid.validateCanonical("12345678-abcd-4ef0-7123-456789abcdef")); // bad variant (7)
    try std.testing.expectError(uuid.UuidError.InvalidVariant, uuid.validateCanonical("12345678-abcd-4ef0-c123-456789abcdef")); // bad variant (c)
    try std.testing.expectError(uuid.UuidError.InvalidChar, uuid.validateCanonical("12345678-abcd-4ef0-8123-456789abcdeG")); // upper case G
    try std.testing.expectError(uuid.UuidError.InvalidChar, uuid.validateCanonical("12345678-abcd-4eF0-8123-456789abcdef")); // upper case F
}

test "validator basic" {
    const validator = @import("validator.zig");

    const test_db_path = "test_valid.db";
    defer _ = std.c.unlink(test_db_path);
    const c = @cImport({
        @cInclude("sqlite3.h");
    });
    var db2: ?*c.sqlite3 = null;
    const rc = c.sqlite3_open_v2(test_db_path, &db2, c.SQLITE_OPEN_READWRITE | c.SQLITE_OPEN_CREATE, null);
    try std.testing.expectEqual(c.SQLITE_OK, rc);

    _ = c.sqlite3_exec(db2, "PRAGMA application_id = 1447906135;", null, null, null);
    _ = c.sqlite3_exec(db2, "PRAGMA user_version = 1;", null, null, null);
    _ = c.sqlite3_exec(db2,
        \\CREATE TABLE storage_metadata_tbl (property TEXT PRIMARY KEY, value TEXT NOT NULL);
        \\INSERT INTO storage_metadata_tbl (property, value) VALUES
        \\('storage_format_id', 'vault.moukaeritai.work.storage'),
        \\('format_major', '1'),
        \\('format_minor', '0'),
        \\('schema_version', '1'),
        \\('required_features', '[]'),
        \\('optional_features', '[]'),
        \\('sqlite_application_id', '1447906135'),
        \\('sqlite_user_version', '1'),
        \\('database_uuid', '00000000-0000-4000-8000-000000000001'),
        \\('created_at_ms', '1234567890'),
        \\('created_by_library', 'test'),
        \\('created_by_version', '1.0');
    , null, null, null);

    _ = c.sqlite3_close(db2);

    try validator.validateReadOnly(test_db_path);
}

test "validator bad pragma" {
    const validator = @import("validator.zig");

    const test_db_path = "test_invalid.db";
    defer _ = std.c.unlink(test_db_path);
    const c = @cImport({
        @cInclude("sqlite3.h");
    });
    var db2: ?*c.sqlite3 = null;
    const rc = c.sqlite3_open_v2(test_db_path, &db2, c.SQLITE_OPEN_READWRITE | c.SQLITE_OPEN_CREATE, null);
    try std.testing.expectEqual(c.SQLITE_OK, rc);

    _ = c.sqlite3_exec(db2, "PRAGMA application_id = 1447906136;", null, null, null); // BAD ID
    _ = c.sqlite3_exec(db2, "PRAGMA user_version = 1;", null, null, null);
    _ = c.sqlite3_exec(db2,
        \\CREATE TABLE storage_metadata_tbl (property TEXT PRIMARY KEY, value TEXT NOT NULL);
    , null, null, null);

    _ = c.sqlite3_close(db2);

    try std.testing.expectError(validator.ValidationError.InvalidPragmaApplicationId, validator.validateReadOnly(test_db_path));
}

test "validator bad metadata" {
    const validator = @import("validator.zig");

    const test_db_path = "test_invalid2.db";
    defer _ = std.c.unlink(test_db_path);
    const c = @cImport({
        @cInclude("sqlite3.h");
    });
    var db2: ?*c.sqlite3 = null;
    const rc = c.sqlite3_open_v2(test_db_path, &db2, c.SQLITE_OPEN_READWRITE | c.SQLITE_OPEN_CREATE, null);
    try std.testing.expectEqual(c.SQLITE_OK, rc);

    _ = c.sqlite3_exec(db2, "PRAGMA application_id = 1447906135;", null, null, null);
    _ = c.sqlite3_exec(db2, "PRAGMA user_version = 1;", null, null, null);
    _ = c.sqlite3_exec(db2,
        \\CREATE TABLE storage_metadata_tbl (property TEXT PRIMARY KEY, value TEXT NOT NULL);
        \\INSERT INTO storage_metadata_tbl (property, value) VALUES
        \\('storage_format_id', 'vault.moukaeritai.work.storage'),
        \\('format_major', '1'),
        \\('format_minor', '0'),
        \\('schema_version', '1'),
        \\('required_features', '["bad"]'),
        \\('optional_features', '[]'),
        \\('sqlite_application_id', '1447906135'),
        \\('sqlite_user_version', '1'),
        \\('database_uuid', '00000000-0000-4000-8000-000000000001'),
        \\('created_at_ms', '1234567890'),
        \\('created_by_library', 'test'),
        \\('created_by_version', '1.0');
    , null, null, null);

    _ = c.sqlite3_close(db2);

    // required_features is not '[]'
    try std.testing.expectError(validator.ValidationError.InvalidMetadataValue, validator.validateReadOnly(test_db_path));
}
