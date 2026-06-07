const std = @import("std");
const sqlite = @import("sqlite.zig");
const uuid = @import("uuid.zig");

pub const ValidationError = error{
    MissingMetadataTable,
    InvalidPragmaApplicationId,
    InvalidPragmaUserVersion,
    MissingMetadataKey,
    InvalidMetadataValue,
    InvalidUuid,
    InvalidTimestamp,
} || sqlite.SQLiteError || uuid.UuidError || std.fmt.ParseIntError;

pub fn validateReadOnly(path: [:0]const u8) !void {
    var db = try sqlite.Database.openReadOnly(path);
    defer db.close();

    try db.exec("PRAGMA foreign_keys = ON");

    // Check application_id
    const app_id = try db.queryPragmaInt("PRAGMA application_id");
    if (app_id != 1447906135) {
        return ValidationError.InvalidPragmaApplicationId;
    }

    // Check user_version
    const user_version = try db.queryPragmaInt("PRAGMA user_version");
    if (user_version != 1) {
        return ValidationError.InvalidPragmaUserVersion;
    }

    // Check table exists
    if (!try db.checkTableExists("storage_metadata_tbl")) {
        return ValidationError.MissingMetadataTable;
    }

    // Fetch and validate metadata
    var stmt = try sqlite.Statement.prepare(&db, "SELECT property, value FROM storage_metadata_tbl");
    defer stmt.finalize();


    var allocator = std.heap.page_allocator;
    var metadata = std.StringHashMap([]const u8).init(allocator);
    defer {
        var it = metadata.iterator();
        while (it.next()) |entry| {
            allocator.free(entry.key_ptr.*);
            allocator.free(entry.value_ptr.*);
        }
        metadata.deinit();
    }

    while (try stmt.step()) {
        const prop = stmt.columnText(0);
        const val = stmt.columnText(1);
        if (prop != null and val != null) {
            const dup_prop = try allocator.dupe(u8, prop.?);
            // Handle error in second dupe correctly by freeing the first
            const dup_val = allocator.dupe(u8, val.?) catch |err| {
                allocator.free(dup_prop);
                return err;
            };
            metadata.put(dup_prop, dup_val) catch |err| {
                allocator.free(dup_prop);
                allocator.free(dup_val);
                return err;
            };

        }
    }

    // Validate specific metadata
    try expectMetadataValue(&metadata, "storage_format_id", "vault.moukaeritai.work.storage");
    try expectMetadataValue(&metadata, "format_major", "1");
    try expectMetadataValue(&metadata, "format_minor", "0");
    try expectMetadataValue(&metadata, "schema_version", "1");
    try expectMetadataValue(&metadata, "required_features", "[]");
    try expectMetadataValue(&metadata, "optional_features", "[]");
    try expectMetadataValue(&metadata, "sqlite_application_id", "1447906135");
    try expectMetadataValue(&metadata, "sqlite_user_version", "1");

    // UUID
    if (metadata.get("database_uuid")) |val| {
        uuid.validateCanonical(val) catch return ValidationError.InvalidUuid;
    } else {
        return ValidationError.MissingMetadataKey;
    }

    // Timestamps
    if (metadata.get("created_at_ms")) |val| {
        if (!isCanonicalTimestamp(val)) return ValidationError.InvalidTimestamp;
    } else {
        return ValidationError.MissingMetadataKey;
    }

    // Created by
    if (metadata.get("created_by_library")) |val| {
        if (val.len == 0) return ValidationError.InvalidMetadataValue;
    } else {
        return ValidationError.MissingMetadataKey;
    }

    if (metadata.get("created_by_version")) |val| {
        if (val.len == 0) return ValidationError.InvalidMetadataValue;
    } else {
        return ValidationError.MissingMetadataKey;
    }
}

fn expectMetadataValue(metadata: *std.StringHashMap([]const u8), key: []const u8, expected: []const u8) !void {
    if (metadata.get(key)) |val| {
        if (!std.mem.eql(u8, val, expected)) {
            return ValidationError.InvalidMetadataValue;
        }
    } else {
        return ValidationError.MissingMetadataKey;
    }
}

fn isCanonicalTimestamp(val: []const u8) bool {
    if (val.len == 0) return false;
    if (val.len > 1 and val[0] == '0') return false; // leading zeros not allowed for multi-digit
    for (val) |char| {
        if (char < '0' or char > '9') return false;
    }
    return true;
}
