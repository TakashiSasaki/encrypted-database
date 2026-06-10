const std = @import("std");
const sqlite = @import("sqlite.zig");
const jcs = @import("jcs.zig");
const hex = @import("hex.zig");
const aad = @import("aad.zig");

// Helper for generating UUID v4
pub fn generateUuid(allocator: std.mem.Allocator, io: std.Io) ![]u8 {
    var bytes: [16]u8 = undefined;
    try io.randomSecure(&bytes);
    // Set UUID v4
    bytes[6] = (bytes[6] & 0x0f) | 0x40;
    // Set RFC4122 variant
    bytes[8] = (bytes[8] & 0x3f) | 0x80;

    const out = try allocator.alloc(u8, 36);
    errdefer allocator.free(out);

    _ = try std.fmt.bufPrint(out, "{x:0>2}{x:0>2}{x:0>2}{x:0>2}-{x:0>2}{x:0>2}-{x:0>2}{x:0>2}-{x:0>2}{x:0>2}-{x:0>2}{x:0>2}{x:0>2}{x:0>2}{x:0>2}{x:0>2}", .{
        bytes[0], bytes[1], bytes[2], bytes[3],
        bytes[4], bytes[5],
        bytes[6], bytes[7],
        bytes[8], bytes[9],
        bytes[10], bytes[11], bytes[12], bytes[13], bytes[14], bytes[15],
    });
    return out;
}

pub const WriterError = anyerror;

pub const Writer = struct {
    allocator: std.mem.Allocator,
    db: sqlite.Database,
    active_db_kek: [32]u8,
    active_db_kid: []u8,

    pub fn close(self: *Writer) void {
        self.db.close();
        self.allocator.free(self.active_db_kid);
    }

    pub fn storePayload(self: *Writer, io: std.Io, schema_uuid: []const u8, content_type: []const u8, payload_json: []const u8) ![]u8 {
        return storePayloadImpl(self, io, schema_uuid, content_type, payload_json);
    }

    pub fn updatePayload(self: *Writer, io: std.Io, object_uuid: []const u8, schema_uuid: []const u8, content_type: []const u8, payload_json: []const u8) !void {
        return updatePayloadImpl(self, io, object_uuid, schema_uuid, content_type, payload_json);
    }

    pub fn deletePayload(self: *Writer, object_uuid: []const u8) !void {
        return deletePayloadImpl(self, object_uuid);
    }
};

pub fn isValidContentType(content_type: []const u8) bool {
    if (content_type.len == 0) return false;
    for (content_type) |c| {
        if (std.ascii.isControl(c)) return false;
    }
    var it = std.mem.splitScalar(u8, content_type, '/');
    const ty = it.next() orelse "";
    const subtype = it.next() orelse "";
    if (ty.len == 0 or subtype.len == 0) return false;
    return true;
}

pub fn createNew(allocator: std.mem.Allocator, io: std.Io, db_path: [:0]const u8, passphrase: []const u8, platform: []const u8) !Writer {
    if (passphrase.len == 0) return WriterError.EmptyPassphrase;

    const schema_path_c = std.c.getenv("VAULT_SCHEMA_SQL_PATH") orelse return WriterError.MissingEnvSchemaPath;
    const schema_path_len = std.mem.len(schema_path_c);
    const schema_path = schema_path_c[0..schema_path_len];

    const cwd = std.Io.Dir.cwd();
    const schema_sql = cwd.readFileAlloc(io, schema_path, allocator, .limited(1024 * 1024)) catch return WriterError.MissingSchemaFile;
    defer allocator.free(schema_sql);

    // ensure null-terminated schema sql for c ABI
    const schema_sql_z = try allocator.dupeZ(u8, schema_sql);
    defer allocator.free(schema_sql_z);

    var db = try sqlite.Database.openReadWriteCreate(db_path);
    errdefer db.close();

    try db.exec("PRAGMA page_size = 4096");
    try db.exec("PRAGMA auto_vacuum = NONE");
    try db.exec("PRAGMA foreign_keys = ON");

    // optional pragmas
    db.exec("PRAGMA journal_mode = WAL") catch |err| {
        std.debug.print("Warning: Failed to enable WAL mode: {}\n", .{err});
    };
    db.exec("PRAGMA synchronous = NORMAL") catch {};

    try db.exec("BEGIN TRANSACTION");
    errdefer db.exec("ROLLBACK") catch {};

    try db.exec(schema_sql_z);
    try db.exec("PRAGMA application_id = 1447906135");
    try db.exec("PRAGMA user_version = 1");

    // Validate platform
    {
        var stmt = try sqlite.Statement.prepare(&db, "SELECT platform FROM platform_tbl WHERE platform = ?1");
        defer stmt.finalize();
        try stmt.bindText(1, platform);
        if (!try stmt.step()) {
            return WriterError.UnsupportedPlatform;
        }
    }

    const now_ms: i64 = 1700000000000; // fixed test-only timestamp for Zig write-matrix scaffold

    const db_uuid = try generateUuid(allocator, io);
    defer allocator.free(db_uuid);

    // Insert metadata
    {
        var stmt = try sqlite.Statement.prepare(&db, "INSERT INTO storage_metadata_tbl (property, value) VALUES (?1, ?2)");
        defer stmt.finalize();

        const props = [_]struct { prop: []const u8, val: []const u8 }{
            .{ .prop = "storage_format_id", .val = "vault.moukaeritai.work.storage" },
            .{ .prop = "format_major", .val = "1" },
            .{ .prop = "format_minor", .val = "0" },
            .{ .prop = "schema_version", .val = "1" },
            .{ .prop = "required_features", .val = "[]" },
            .{ .prop = "optional_features", .val = "[]" },
            .{ .prop = "sqlite_application_id", .val = "1447906135" },
            .{ .prop = "sqlite_user_version", .val = "1" },
            .{ .prop = "database_uuid", .val = db_uuid },
        };
        for (props) |p| {
            try stmt.bindText(1, p.prop);
            try stmt.bindText(2, p.val);
            _ = try stmt.step();
            try stmt.reset();
        }

        var buf: [64]u8 = undefined;
        const now_str = try std.fmt.bufPrint(&buf, "{}", .{now_ms});
        try stmt.bindText(1, "created_at_ms");
        try stmt.bindText(2, now_str);
        _ = try stmt.step();
        try stmt.reset();

        try stmt.bindText(1, "created_by_library");
        try stmt.bindText(2, "zig-writer-scaffold");
        _ = try stmt.step();
        try stmt.reset();

        try stmt.bindText(1, "created_by_version");
        try stmt.bindText(2, "0.1.0");
        _ = try stmt.step();
        try stmt.reset();
    }

    const unlock_kid = try generateUuid(allocator, io);
    defer allocator.free(unlock_kid);

    var salt: [16]u8 = undefined;
    try io.randomSecure(&salt);
    var salt_b64_buf: [32]u8 = undefined;
    const salt_b64_str = std.base64.url_safe_no_pad.Encoder.encode(&salt_b64_buf, &salt);

    var config_map = std.json.ObjectMap{};
    defer config_map.deinit(allocator);

    try config_map.put(allocator, "v", std.json.Value{ .integer = 1 });
    try config_map.put(allocator, "profile", std.json.Value{ .string = "argon2id-profile-v1" });
    try config_map.put(allocator, "kdf", std.json.Value{ .string = "argon2id" });
    try config_map.put(allocator, "memory_kib", std.json.Value{ .integer = 65536 });
    try config_map.put(allocator, "iterations", std.json.Value{ .integer = 3 });
    try config_map.put(allocator, "parallelism", std.json.Value{ .integer = 1 });
    try config_map.put(allocator, "output_bytes", std.json.Value{ .integer = 32 });
    try config_map.put(allocator, "salt", std.json.Value{ .string = salt_b64_str });

    const provider_config_json = try jcs.stringifyJCS(allocator, std.json.Value{ .object = config_map });
    defer allocator.free(provider_config_json);

    // KDF
    var unlock_kek: [32]u8 = undefined;
    try std.crypto.pwhash.argon2.kdf(allocator, &unlock_kek, passphrase, &salt, .{
        .t = 3,
        .m = 65536,
        .p = 1,
    }, .argon2id, io);

    const db_kid = try generateUuid(allocator, io);
    // caller of CreateNew must free writer, writer owns active_db_kid
    const db_kid_owned = try allocator.dupe(u8, db_kid);
    defer allocator.free(db_kid);

    var db_kek: [32]u8 = undefined;
    try io.randomSecure(&db_kek);

    const alg = "A256GCM";
    const wrap_aad_policy = "wrap-database-key-v1";

    // AAD for wrap
    var wrap_aad_map = std.json.ObjectMap{};
    defer wrap_aad_map.deinit(allocator);
    try wrap_aad_map.put(allocator, "v", std.json.Value{ .integer = 1 });
    try wrap_aad_map.put(allocator, "aad_policy", std.json.Value{ .string = wrap_aad_policy });
    try wrap_aad_map.put(allocator, "wrapped_kid", std.json.Value{ .string = db_kid });
    try wrap_aad_map.put(allocator, "wrapping_kid", std.json.Value{ .string = unlock_kid });
    const wrap_aad_bytes = try jcs.stringifyJCS(allocator, std.json.Value{ .object = wrap_aad_map });
    defer allocator.free(wrap_aad_bytes);

    var wrap_nonce: [12]u8 = undefined;
    try io.randomSecure(&wrap_nonce);

    var wrapped_db_kek: [32]u8 = undefined;
    var wrap_tag: [16]u8 = undefined;
    std.crypto.aead.aes_gcm.Aes256Gcm.encrypt(&wrapped_db_kek, &wrap_tag, &db_kek, wrap_aad_bytes, wrap_nonce, unlock_kek);

    // concatenate for db storage (ciphertext + tag)
    const wrapped_db_kek_full = try allocator.alloc(u8, 48);
    defer allocator.free(wrapped_db_kek_full);
    @memcpy(wrapped_db_kek_full[0..32], &wrapped_db_kek);
    @memcpy(wrapped_db_kek_full[32..48], &wrap_tag);

    const wrap_id = try generateUuid(allocator, io);
    defer allocator.free(wrap_id);

    {
        var stmt = try sqlite.Statement.prepare(&db, "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)");
        defer stmt.finalize();

        // Unlock KEK
        try stmt.bindText(1, unlock_kid);
        try stmt.bindText(2, "unlock_kek");
        try stmt.bindText(3, "wrap_database_keys");
        try stmt.bindText(4, alg);
        try stmt.bindText(5, "active");
        try stmt.bindInt64(6, now_ms);
        _ = try stmt.step();
        try stmt.reset();

        // DB KEK
        try stmt.bindText(1, db_kid);
        try stmt.bindText(2, "database_kek");
        try stmt.bindText(3, "wrap_record_keys");
        try stmt.bindText(4, alg);
        try stmt.bindText(5, "active");
        try stmt.bindInt64(6, now_ms);
        _ = try stmt.step();
    }

    {
        var stmt = try sqlite.Statement.prepare(&db, "INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?1, ?2, ?3, ?4)");
        defer stmt.finalize();
        try stmt.bindText(1, unlock_kid);
        try stmt.bindText(2, "passphrase_argon2id");
        try stmt.bindText(3, provider_config_json);
        try stmt.bindText(4, platform);
        _ = try stmt.step();
    }

    {
        var stmt = try sqlite.Statement.prepare(&db, "INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)");
        defer stmt.finalize();
        try stmt.bindText(1, wrap_id);
        try stmt.bindText(2, db_kid);
        try stmt.bindText(3, unlock_kid);
        try stmt.bindInt64(4, 1);
        try stmt.bindText(5, "key_wrap");
        try stmt.bindText(6, alg);
        try stmt.bindBlob(7, &wrap_nonce);
        try stmt.bindBlob(8, wrapped_db_kek_full);
        try stmt.bindText(9, wrap_aad_policy);
        try stmt.bindInt64(10, now_ms);
        _ = try stmt.step();
    }

    try db.exec("COMMIT");

    return Writer{
        .allocator = allocator,
        .db = db,
        .active_db_kek = db_kek,
        .active_db_kid = db_kid_owned,
    };
}

pub fn storePayloadImpl(self: *Writer, io: std.Io, schema_uuid: []const u8, content_type: []const u8, payload_json: []const u8) ![]u8 {
    if (!isValidContentType(content_type)) return WriterError.RequirementError;

    // canonicalize payload json
    var parsed_payload = try std.json.parseFromSlice(std.json.Value, self.allocator, payload_json, .{});
    defer parsed_payload.deinit();
    const canonical_payload = try jcs.stringifyJCS(self.allocator, parsed_payload.value);
    defer self.allocator.free(canonical_payload);

    const object_uuid = try generateUuid(self.allocator, io);
    // caller frees object_uuid

    var record_dek_bytes: [32]u8 = undefined;
    try io.randomSecure(&record_dek_bytes);

    const record_kid = try generateUuid(self.allocator, io);
    defer self.allocator.free(record_kid);

    const alg = "A256GCM";
    const wrap_aad_policy = "wrap-record-key-v1";

    var wrap_aad_map = std.json.ObjectMap{};
    defer wrap_aad_map.deinit(self.allocator);
    try wrap_aad_map.put(self.allocator, "v", std.json.Value{ .integer = 1 });
    try wrap_aad_map.put(self.allocator, "aad_policy", std.json.Value{ .string = wrap_aad_policy });
    try wrap_aad_map.put(self.allocator, "wrapped_kid", std.json.Value{ .string = record_kid });
    try wrap_aad_map.put(self.allocator, "wrapping_kid", std.json.Value{ .string = self.active_db_kid });
    const wrap_aad_bytes = try jcs.stringifyJCS(self.allocator, std.json.Value{ .object = wrap_aad_map });
    defer self.allocator.free(wrap_aad_bytes);

    var wrap_nonce: [12]u8 = undefined;
    try io.randomSecure(&wrap_nonce);

    var wrapped_record_dek: [32]u8 = undefined;
    var wrap_tag: [16]u8 = undefined;
    std.crypto.aead.aes_gcm.Aes256Gcm.encrypt(&wrapped_record_dek, &wrap_tag, &record_dek_bytes, wrap_aad_bytes, wrap_nonce, self.active_db_kek);

    const wrapped_record_dek_full = try self.allocator.alloc(u8, 48);
    defer self.allocator.free(wrapped_record_dek_full);
    @memcpy(wrapped_record_dek_full[0..32], &wrapped_record_dek);
    @memcpy(wrapped_record_dek_full[32..48], &wrap_tag);

    const payload_aad_policy = "record-payload-v1";
    var payload_aad_map = std.json.ObjectMap{};
    defer payload_aad_map.deinit(self.allocator);
    try payload_aad_map.put(self.allocator, "v", std.json.Value{ .integer = 1 });
    try payload_aad_map.put(self.allocator, "aad_policy", std.json.Value{ .string = payload_aad_policy });
    try payload_aad_map.put(self.allocator, "object_uuid", std.json.Value{ .string = object_uuid });
    try payload_aad_map.put(self.allocator, "schema_uuid", std.json.Value{ .string = schema_uuid });
    try payload_aad_map.put(self.allocator, "content_type", std.json.Value{ .string = content_type });
    try payload_aad_map.put(self.allocator, "kid", std.json.Value{ .string = record_kid });
    try payload_aad_map.put(self.allocator, "alg", std.json.Value{ .string = alg });
    const payload_aad_bytes = try jcs.stringifyJCS(self.allocator, std.json.Value{ .object = payload_aad_map });
    defer self.allocator.free(payload_aad_bytes);

    var payload_nonce: [12]u8 = undefined;
    try io.randomSecure(&payload_nonce);

    const ciphertext_only = try self.allocator.alloc(u8, canonical_payload.len);
    defer self.allocator.free(ciphertext_only);
    var payload_tag: [16]u8 = undefined;

    std.crypto.aead.aes_gcm.Aes256Gcm.encrypt(ciphertext_only, &payload_tag, canonical_payload, payload_aad_bytes, payload_nonce, record_dek_bytes);

    const ciphertext_full = try self.allocator.alloc(u8, canonical_payload.len + 16);
    defer self.allocator.free(ciphertext_full);
    @memcpy(ciphertext_full[0..canonical_payload.len], ciphertext_only);
    @memcpy(ciphertext_full[canonical_payload.len..], &payload_tag);

    const now_ms: i64 = 1700000000000; // fixed test-only timestamp for Zig write-matrix scaffold
    const wrap_id = try generateUuid(self.allocator, io);
    defer self.allocator.free(wrap_id);

    try self.db.exec("BEGIN TRANSACTION");
    errdefer self.db.exec("ROLLBACK") catch {};

    {
        var stmt = try sqlite.Statement.prepare(&self.db, "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6)");
        defer stmt.finalize();
        try stmt.bindText(1, record_kid);
        try stmt.bindText(2, "record_dek");
        try stmt.bindText(3, "encrypt_payload");
        try stmt.bindText(4, alg);
        try stmt.bindText(5, "active");
        try stmt.bindInt64(6, now_ms);
        _ = try stmt.step();
    }

    {
        var stmt = try sqlite.Statement.prepare(&self.db, "INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10)");
        defer stmt.finalize();
        try stmt.bindText(1, wrap_id);
        try stmt.bindText(2, record_kid);
        try stmt.bindText(3, self.active_db_kid);
        try stmt.bindInt64(4, 1);
        try stmt.bindText(5, "key_wrap");
        try stmt.bindText(6, alg);
        try stmt.bindBlob(7, &wrap_nonce);
        try stmt.bindBlob(8, wrapped_record_dek_full);
        try stmt.bindText(9, wrap_aad_policy);
        try stmt.bindInt64(10, now_ms);
        _ = try stmt.step();
    }

    {
        var stmt = try sqlite.Statement.prepare(&self.db, "INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9, ?10, ?11, ?12)");
        defer stmt.finalize();
        try stmt.bindText(1, object_uuid);
        try stmt.bindInt64(2, 1);
        try stmt.bindText(3, "aead");
        try stmt.bindText(4, schema_uuid);
        try stmt.bindText(5, content_type);
        try stmt.bindText(6, alg);
        try stmt.bindText(7, record_kid);
        try stmt.bindBlob(8, &payload_nonce);
        try stmt.bindBlob(9, ciphertext_full);
        try stmt.bindText(10, payload_aad_policy);
        try stmt.bindInt64(11, now_ms);
        try stmt.bindInt64(12, now_ms);
        _ = try stmt.step();
    }

    try self.db.exec("COMMIT");
    return object_uuid;
}

pub fn updatePayloadImpl(self: *Writer, io: std.Io, object_uuid: []const u8, schema_uuid: []const u8, content_type: []const u8, payload_json: []const u8) !void {
    if (!isValidContentType(content_type)) return WriterError.RequirementError;

    var tx_started = false;
    try self.db.exec("BEGIN TRANSACTION");
    tx_started = true;
    errdefer if (tx_started) { self.db.exec("ROLLBACK") catch {}; };

    var record_kid: []u8 = undefined;
    var alg: []u8 = undefined;
    var created_at_ms: i64 = 0;

    {
        var stmt = try sqlite.Statement.prepare(&self.db, "SELECT kid, alg, created_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?1");
        defer stmt.finalize();
        try stmt.bindText(1, object_uuid);
        if (!try stmt.step()) {
            return WriterError.NotFound;
        }
        record_kid = try self.allocator.dupe(u8, stmt.columnText(0) orelse "");
        alg = try self.allocator.dupe(u8, stmt.columnText(1) orelse "");
        created_at_ms = stmt.columnInt64(2);
    }
    defer self.allocator.free(record_kid);
    defer self.allocator.free(alg);

    if (!std.mem.eql(u8, alg, "A256GCM")) return WriterError.RequirementError;

    {
        var stmt = try sqlite.Statement.prepare(&self.db, "SELECT status FROM key_tbl WHERE kid = ?1 AND key_class = 'record_dek'");
        defer stmt.finalize();
        try stmt.bindText(1, record_kid);
        if (!try stmt.step()) {
            return WriterError.NotFound;
        }
        const status = stmt.columnText(0) orelse "";
        if (!std.mem.eql(u8, status, "active")) return WriterError.RequirementError;
    }

    var envelope_v: i64 = 0;
    var envelope_type: []u8 = undefined;
    var wrap_alg: []u8 = undefined;
    var nonce_wrap: []u8 = undefined;
    var wrapped_record_dek_full: []u8 = undefined;
    var wrap_aad_policy: []u8 = undefined;

    {
        var stmt = try sqlite.Statement.prepare(&self.db, "SELECT envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ?1 AND wrapping_kid = ?2");
        defer stmt.finalize();
        try stmt.bindText(1, record_kid);
        try stmt.bindText(2, self.active_db_kid);
        if (!try stmt.step()) {
            return WriterError.NotFound;
        }
        envelope_v = stmt.columnInt64(0);
        envelope_type = try self.allocator.dupe(u8, stmt.columnText(1) orelse "");
        wrap_alg = try self.allocator.dupe(u8, stmt.columnText(2) orelse "");
        nonce_wrap = try self.allocator.dupe(u8, stmt.columnBlob(3) orelse "");
        wrapped_record_dek_full = try self.allocator.dupe(u8, stmt.columnBlob(4) orelse "");
        wrap_aad_policy = try self.allocator.dupe(u8, stmt.columnText(5) orelse "");
    }
    defer self.allocator.free(envelope_type);
    defer self.allocator.free(wrap_alg);
    defer self.allocator.free(nonce_wrap);
    defer self.allocator.free(wrapped_record_dek_full);
    defer self.allocator.free(wrap_aad_policy);

    if (envelope_v != 1 or !std.mem.eql(u8, envelope_type, "key_wrap") or !std.mem.eql(u8, wrap_alg, "A256GCM") or !std.mem.eql(u8, wrap_aad_policy, "wrap-record-key-v1")) {
        return WriterError.RequirementError;
    }

    var wrap_aad_map = std.json.ObjectMap{};
    defer wrap_aad_map.deinit(self.allocator);
    try wrap_aad_map.put(self.allocator, "v", std.json.Value{ .integer = 1 });
    try wrap_aad_map.put(self.allocator, "aad_policy", std.json.Value{ .string = wrap_aad_policy });
    try wrap_aad_map.put(self.allocator, "wrapped_kid", std.json.Value{ .string = record_kid });
    try wrap_aad_map.put(self.allocator, "wrapping_kid", std.json.Value{ .string = self.active_db_kid });
    const wrap_aad_bytes = try jcs.stringifyJCS(self.allocator, std.json.Value{ .object = wrap_aad_map });
    defer self.allocator.free(wrap_aad_bytes);

    var record_dek_bytes: [32]u8 = undefined;
    var wrap_tag: [16]u8 = undefined;
    if (wrapped_record_dek_full.len < 16) return WriterError.CryptoError;
    const len_cipher = wrapped_record_dek_full.len - 16;
    @memcpy(&wrap_tag, wrapped_record_dek_full[len_cipher..]);

    std.crypto.aead.aes_gcm.Aes256Gcm.decrypt(&record_dek_bytes, wrapped_record_dek_full[0..len_cipher], wrap_tag, wrap_aad_bytes, nonce_wrap[0..12].*, self.active_db_kek) catch return WriterError.CryptoError;

    // canonicalize payload json
    var parsed_payload = try std.json.parseFromSlice(std.json.Value, self.allocator, payload_json, .{});
    defer parsed_payload.deinit();
    const canonical_payload = try jcs.stringifyJCS(self.allocator, parsed_payload.value);
    defer self.allocator.free(canonical_payload);

    const payload_aad_policy = "record-payload-v1";
    var payload_aad_map = std.json.ObjectMap{};
    defer payload_aad_map.deinit(self.allocator);
    try payload_aad_map.put(self.allocator, "v", std.json.Value{ .integer = 1 });
    try payload_aad_map.put(self.allocator, "aad_policy", std.json.Value{ .string = payload_aad_policy });
    try payload_aad_map.put(self.allocator, "object_uuid", std.json.Value{ .string = object_uuid });
    try payload_aad_map.put(self.allocator, "schema_uuid", std.json.Value{ .string = schema_uuid });
    try payload_aad_map.put(self.allocator, "content_type", std.json.Value{ .string = content_type });
    try payload_aad_map.put(self.allocator, "kid", std.json.Value{ .string = record_kid });
    try payload_aad_map.put(self.allocator, "alg", std.json.Value{ .string = alg });
    const payload_aad_bytes = try jcs.stringifyJCS(self.allocator, std.json.Value{ .object = payload_aad_map });
    defer self.allocator.free(payload_aad_bytes);

    var payload_nonce: [12]u8 = undefined;
    try io.randomSecure(&payload_nonce);

    const ciphertext_only = try self.allocator.alloc(u8, canonical_payload.len);
    defer self.allocator.free(ciphertext_only);
    var payload_tag: [16]u8 = undefined;

    std.crypto.aead.aes_gcm.Aes256Gcm.encrypt(ciphertext_only, &payload_tag, canonical_payload, payload_aad_bytes, payload_nonce, record_dek_bytes);

    const ciphertext_full = try self.allocator.alloc(u8, canonical_payload.len + 16);
    defer self.allocator.free(ciphertext_full);
    @memcpy(ciphertext_full[0..canonical_payload.len], ciphertext_only);
    @memcpy(ciphertext_full[canonical_payload.len..], &payload_tag);

    const now_ms: i64 = 1700000000000; // fixed test-only timestamp for Zig write-matrix scaffold

    {
        var stmt = try sqlite.Statement.prepare(&self.db, "UPDATE encrypted_object_tbl SET schema_uuid = ?1, content_type = ?2, nonce = ?3, ciphertext = ?4, aad_policy = ?5, updated_at_ms = ?6, created_at_ms = ?7 WHERE object_uuid = ?8");
        defer stmt.finalize();
        try stmt.bindText(1, schema_uuid);
        try stmt.bindText(2, content_type);
        try stmt.bindBlob(3, &payload_nonce);
        try stmt.bindBlob(4, ciphertext_full);
        try stmt.bindText(5, payload_aad_policy);
        try stmt.bindInt64(6, now_ms);
        try stmt.bindInt64(7, created_at_ms);
        try stmt.bindText(8, object_uuid);
        _ = try stmt.step();
    }

    try self.db.exec("COMMIT");
    tx_started = false;
}

pub fn deletePayloadImpl(self: *Writer, object_uuid: []const u8) !void {
    try self.db.exec("BEGIN TRANSACTION");
    errdefer self.db.exec("ROLLBACK") catch {};

    var stmt = try sqlite.Statement.prepare(&self.db, "DELETE FROM encrypted_object_tbl WHERE object_uuid = ?1");
    defer stmt.finalize();
    try stmt.bindText(1, object_uuid);

    // SQLite doesn't natively return rows affected from statement step easily in our wrapper.
    // We will just step and commit. If needed we can check existence first.

    var check_stmt = try sqlite.Statement.prepare(&self.db, "SELECT 1 FROM encrypted_object_tbl WHERE object_uuid = ?1");
    defer check_stmt.finalize();
    try check_stmt.bindText(1, object_uuid);
    const exists = try check_stmt.step();

    if (!exists) {
        return WriterError.NotFound;
    }

    _ = try stmt.step();
    try self.db.exec("COMMIT");
}
