const std = @import("std");
const sqlite = @import("sqlite.zig");
const aad_import = @import("aad.zig");
const hex = @import("hex.zig");

pub const ReadOnlyError = error{
    InvalidPassphrase,
    ObjectNotFound,
    UnsupportedProvider,
    UnsupportedAlgorithm,
    UnsupportedEnvelope,
    UnlockFailed,
    KeyUnwrapFailed,
    DecryptFailed,
    InvalidProviderConfig,
    MissingData,
} || sqlite.SQLiteError || std.json.ParseFromValueError || std.json.ParseError(std.json.Scanner) || std.fmt.ParseIntError || std.base64.Error;

pub fn readFixture(allocator: std.mem.Allocator, io: std.Io, db_path: [:0]const u8, passphrase: []const u8, object_uuid: []const u8, expected_hex: []const u8) !void {
    var db = try sqlite.Database.openReadOnly(db_path);
    defer db.close();

    // 1. Get object payload
    const obj_sql = "SELECT envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?";
    var obj_stmt = try sqlite.Statement.prepare(&db, obj_sql);
    defer obj_stmt.finalize();

    try obj_stmt.bindText(1, object_uuid);
    if (!try obj_stmt.step()) {
        std.debug.print("Object not found: {s}\n", .{object_uuid});
        return ReadOnlyError.ObjectNotFound;
    }

    const envelope_v = obj_stmt.columnInt64(0);
    if (envelope_v != 1) return ReadOnlyError.UnsupportedEnvelope;

    const envelope_type = obj_stmt.columnText(1) orelse return ReadOnlyError.MissingData;
    if (!std.mem.eql(u8, envelope_type, "aead")) return ReadOnlyError.UnsupportedEnvelope;

    const schema_uuid = obj_stmt.columnText(2) orelse return ReadOnlyError.MissingData;
    const content_type = obj_stmt.columnText(3) orelse return ReadOnlyError.MissingData;
    const alg = obj_stmt.columnText(4) orelse return ReadOnlyError.MissingData;
    if (!std.mem.eql(u8, alg, "A256GCM")) return ReadOnlyError.UnsupportedAlgorithm;

    const record_kid = obj_stmt.columnText(5) orelse return ReadOnlyError.MissingData;
    const obj_nonce = obj_stmt.columnBlob(6) orelse return ReadOnlyError.MissingData;
    const obj_ciphertext = obj_stmt.columnBlob(7) orelse return ReadOnlyError.MissingData;
    const obj_aad_policy = obj_stmt.columnText(8) orelse return ReadOnlyError.MissingData;

    // Dup data since we will finalize/step other queries
    const obj_schema_uuid = try allocator.dupe(u8, schema_uuid); defer allocator.free(obj_schema_uuid);
    const obj_content_type = try allocator.dupe(u8, content_type); defer allocator.free(obj_content_type);
    const obj_kid = try allocator.dupe(u8, record_kid); defer allocator.free(obj_kid);
    const obj_alg = try allocator.dupe(u8, alg); defer allocator.free(obj_alg);
    const obj_nonce_dup = try allocator.dupe(u8, obj_nonce); defer allocator.free(obj_nonce_dup);
    const obj_ciphertext_dup = try allocator.dupe(u8, obj_ciphertext); defer allocator.free(obj_ciphertext_dup);
    const obj_aad_policy_dup = try allocator.dupe(u8, obj_aad_policy); defer allocator.free(obj_aad_policy_dup);

    // 2. Resolve database_kek wrapping the record_dek (ensuring it is active)
    const dek_wrap_sql = "SELECT w.wrapping_kid, w.wrap_alg, w.nonce, w.wrapped_key, w.aad_policy FROM wrapped_key_tbl w JOIN key_tbl k ON w.wrapping_kid = k.kid WHERE w.wrapped_kid = ? AND k.status = 'active'";
    var dek_stmt = try sqlite.Statement.prepare(&db, dek_wrap_sql);
    defer dek_stmt.finalize();

    try dek_stmt.bindText(1, obj_kid);
    if (!try dek_stmt.step()) return ReadOnlyError.MissingData;

    const database_kid = try allocator.dupe(u8, dek_stmt.columnText(0) orelse return ReadOnlyError.MissingData); defer allocator.free(database_kid);
    const dek_wrap_alg = try allocator.dupe(u8, dek_stmt.columnText(1) orelse return ReadOnlyError.MissingData); defer allocator.free(dek_wrap_alg);
    const dek_nonce = try allocator.dupe(u8, dek_stmt.columnBlob(2) orelse return ReadOnlyError.MissingData); defer allocator.free(dek_nonce);
    const dek_wrapped_key = try allocator.dupe(u8, dek_stmt.columnBlob(3) orelse return ReadOnlyError.MissingData); defer allocator.free(dek_wrapped_key);
    const dek_aad_policy = try allocator.dupe(u8, dek_stmt.columnText(4) orelse return ReadOnlyError.MissingData); defer allocator.free(dek_aad_policy);

    // 3. Resolve unlock_kek wrapping the database_kek (ensuring it is active)
    const kek_wrap_sql = "SELECT w.wrapping_kid, w.wrap_alg, w.nonce, w.wrapped_key, w.aad_policy FROM wrapped_key_tbl w JOIN key_tbl k ON w.wrapping_kid = k.kid WHERE w.wrapped_kid = ? AND k.status = 'active'";
    var kek_stmt = try sqlite.Statement.prepare(&db, kek_wrap_sql);
    defer kek_stmt.finalize();

    try kek_stmt.bindText(1, database_kid);
    if (!try kek_stmt.step()) return ReadOnlyError.MissingData;

    const unlock_kid = try allocator.dupe(u8, kek_stmt.columnText(0) orelse return ReadOnlyError.MissingData); defer allocator.free(unlock_kid);
    const kek_wrap_alg = try allocator.dupe(u8, kek_stmt.columnText(1) orelse return ReadOnlyError.MissingData); defer allocator.free(kek_wrap_alg);
    const kek_nonce = try allocator.dupe(u8, kek_stmt.columnBlob(2) orelse return ReadOnlyError.MissingData); defer allocator.free(kek_nonce);
    const kek_wrapped_key = try allocator.dupe(u8, kek_stmt.columnBlob(3) orelse return ReadOnlyError.MissingData); defer allocator.free(kek_wrapped_key);
    const kek_aad_policy = try allocator.dupe(u8, kek_stmt.columnText(4) orelse return ReadOnlyError.MissingData); defer allocator.free(kek_aad_policy);

    // 4. Get unlock provider config
    const provider_sql = "SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?";
    var provider_stmt = try sqlite.Statement.prepare(&db, provider_sql);
    defer provider_stmt.finalize();

    try provider_stmt.bindText(1, unlock_kid);
    if (!try provider_stmt.step()) return ReadOnlyError.MissingData;

    const unlock_provider = provider_stmt.columnText(0) orelse return ReadOnlyError.MissingData;
    if (!std.mem.eql(u8, unlock_provider, "passphrase_argon2id")) return ReadOnlyError.UnsupportedProvider;

    const provider_config_json = provider_stmt.columnText(1) orelse return ReadOnlyError.MissingData;
    var parsed = try std.json.parseFromSlice(std.json.Value, allocator, provider_config_json, .{});
    defer parsed.deinit();

    const jcs_import = @import("jcs.zig");
    const canonical_config_json = try jcs_import.stringifyJCS(allocator, parsed.value);
    defer allocator.free(canonical_config_json);

    if (!std.mem.eql(u8, provider_config_json, canonical_config_json)) {
        return ReadOnlyError.InvalidProviderConfig;
    }

    const config = parsed.value.object;
    const kdf = config.get("kdf").?.string;
    if (!std.mem.eql(u8, kdf, "argon2id")) return ReadOnlyError.InvalidProviderConfig;

    const profile = config.get("profile").?.string;
    if (!std.mem.eql(u8, profile, "argon2id-profile-v1")) return ReadOnlyError.InvalidProviderConfig;

    const salt_b64 = config.get("salt").?.string;
    const memory_kib = @as(u32, @intCast(config.get("memory_kib").?.integer));
    const iterations = @as(u32, @intCast(config.get("iterations").?.integer));
    const parallelism = @as(u24, @intCast(config.get("parallelism").?.integer));
    const output_bytes = @as(u32, @intCast(config.get("output_bytes").?.integer));

    if (output_bytes != 32 or memory_kib != 65536 or iterations != 3 or parallelism != 1) return ReadOnlyError.InvalidProviderConfig;

    const decoder = std.base64.url_safe_no_pad.Decoder;
    const salt_len = try decoder.calcSizeForSlice(salt_b64);
    if (salt_len != 16) return ReadOnlyError.InvalidProviderConfig;

    const salt = try allocator.alloc(u8, salt_len);
    defer allocator.free(salt);
    decoder.decode(salt, salt_b64) catch |err| {
        std.debug.print("Salt decode failed: {}\n", .{err});
        return ReadOnlyError.InvalidProviderConfig;
    };

    // 5. Derive Unlock KEK
    var unlock_kek: [32]u8 = undefined;
    const argon2 = std.crypto.pwhash.argon2;
    try argon2.kdf(allocator, &unlock_kek, passphrase, salt, .{
        .t = iterations,
        .m = memory_kib,
        .p = parallelism,
    }, .argon2id, io);

    // 6. Unwrap Database KEK
    const db_kek = try unwrapKey(allocator, unlock_kek, database_kid, unlock_kid, kek_wrapped_key, kek_nonce, kek_aad_policy);
    defer allocator.free(db_kek);

    // 7. Unwrap Record DEK
    const record_dek = try unwrapKey(allocator, db_kek[0..32].*, obj_kid, database_kid, dek_wrapped_key, dek_nonce, dek_aad_policy);
    defer allocator.free(record_dek);

    // 8. Decrypt Payload
    var obj_context: std.json.ObjectMap = .empty;
    defer obj_context.deinit(allocator);
    try obj_context.put(allocator, "v", std.json.Value{ .integer = 1 });
    try obj_context.put(allocator, "aad_policy", std.json.Value{ .string = obj_aad_policy_dup });
    try obj_context.put(allocator, "alg", std.json.Value{ .string = obj_alg });
    try obj_context.put(allocator, "content_type", std.json.Value{ .string = obj_content_type });
    try obj_context.put(allocator, "kid", std.json.Value{ .string = obj_kid });
    try obj_context.put(allocator, "object_uuid", std.json.Value{ .string = object_uuid });
    try obj_context.put(allocator, "schema_uuid", std.json.Value{ .string = obj_schema_uuid });

    const obj_aad = try aad_import.constructAAD(allocator, std.json.Value{ .object = obj_context });
    defer allocator.free(obj_aad);

    if (obj_ciphertext_dup.len < 16) return ReadOnlyError.DecryptFailed;
    const ciphertext_only = obj_ciphertext_dup[0 .. obj_ciphertext_dup.len - 16];
    const tag_only = obj_ciphertext_dup[obj_ciphertext_dup.len - 16 ..];

    const payload = try allocator.alloc(u8, ciphertext_only.len);
    defer allocator.free(payload);

    std.crypto.aead.aes_gcm.Aes256Gcm.decrypt(payload, ciphertext_only, tag_only[0..16].*, obj_aad, obj_nonce_dup[0..12].*, record_dek[0..32].*) catch |err| {
        std.debug.print("Payload decrypt failed: {}\n", .{err});
        return ReadOnlyError.DecryptFailed;
    };

    // 9. Compare with Expected Hex
    const actual_hex = try hex.encodeHex(allocator, payload);
    defer allocator.free(actual_hex);

    // uppercase or lowercase check, safely do a case insensitive or lower
    const actual_lower = try allocator.dupe(u8, actual_hex);
    defer allocator.free(actual_lower);
    for (actual_lower) |*c| {
        c.* = std.ascii.toLower(c.*);
    }

    const expected_lower = try allocator.dupe(u8, expected_hex);
    defer allocator.free(expected_lower);
    for (expected_lower) |*c| {
        c.* = std.ascii.toLower(c.*);
    }

    if (!std.mem.eql(u8, actual_lower, expected_lower)) {
        std.debug.print("Payload mismatch.\nExpected: {s}\nActual:   {s}\n", .{ expected_lower, actual_lower });
        return ReadOnlyError.DecryptFailed;
    }
}

fn unwrapKey(allocator: std.mem.Allocator, wrapping_key: [32]u8, wrapped_kid: []const u8, wrapping_kid: []const u8, wrapped_key_blob: []const u8, nonce: []const u8, aad_policy: []const u8) ![]u8 {
    var context_map: std.json.ObjectMap = .empty;
    defer context_map.deinit(allocator);
    try context_map.put(allocator, "v", std.json.Value{ .integer = 1 });
    try context_map.put(allocator, "aad_policy", std.json.Value{ .string = aad_policy });
    try context_map.put(allocator, "wrapped_kid", std.json.Value{ .string = wrapped_kid });
    try context_map.put(allocator, "wrapping_kid", std.json.Value{ .string = wrapping_kid });

    const aad = try aad_import.constructAAD(allocator, std.json.Value{ .object = context_map });
    defer allocator.free(aad);

    if (wrapped_key_blob.len < 16) return ReadOnlyError.KeyUnwrapFailed;
    const ciphertext = wrapped_key_blob[0 .. wrapped_key_blob.len - 16];
    const tag = wrapped_key_blob[wrapped_key_blob.len - 16 ..];

    const plaintext = try allocator.alloc(u8, ciphertext.len);

    std.crypto.aead.aes_gcm.Aes256Gcm.decrypt(plaintext, ciphertext, tag[0..16].*, aad, nonce[0..12].*, wrapping_key) catch |err| {
        allocator.free(plaintext);
        std.debug.print("Unwrap failed: {}\n", .{err});
        return ReadOnlyError.KeyUnwrapFailed;
    };
    return plaintext;
}
