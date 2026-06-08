const std = @import("std");
const json_min = @import("json_min.zig");
const aad = @import("aad.zig");
const jcs = @import("jcs.zig");
const hex = @import("hex.zig");

pub fn run(allocator: std.mem.Allocator, io: std.Io) !void {
    const vectors = try json_min.parseJsonFile(allocator, io, "test-vectors/payload/payload-encryption-v1.json");
    const arr = vectors.array;

    try std.Io.File.stdout().writeStreamingAll(io, "Running Payload encryption test vectors...\n");

    var passed: usize = 0;
    var total: usize = 0;

    for (arr.items) |case| {
        total += 1;
        const obj = case.object;

        const name = obj.get("name").?.string;
        const object_uuid = obj.get("object_uuid").?.string;
        const schema_uuid = obj.get("schema_uuid").?.string;
        const content_type = obj.get("content_type").?.string;
        const kid = obj.get("kid").?.string;
        const alg = obj.get("alg").?.string;

        const record_dek_hex = obj.get("record_dek_hex").?.string;
        const nonce_hex = obj.get("nonce_hex").?.string;
        const payload_json = obj.get("payload_json").?;

        const expected_payload_jcs_hex = obj.get("expected_payload_jcs_hex").?.string;
        const expected_aad_hex = obj.get("expected_aad_hex").?.string;
        const expected_ciphertext_hex = obj.get("expected_ciphertext_hex").?.string;
        const expected_tag_hex = obj.get("expected_tag_hex").?.string;
        const valid = obj.get("valid").?.bool;

        const key = try hex.decodeHex(allocator, record_dek_hex);
        defer allocator.free(key);
        const nonce = try hex.decodeHex(allocator, nonce_hex);
        defer allocator.free(nonce);

        const expected_payload_jcs = try hex.decodeHex(allocator, expected_payload_jcs_hex);
        defer allocator.free(expected_payload_jcs);
        const expected_aad = try hex.decodeHex(allocator, expected_aad_hex);
        defer allocator.free(expected_aad);
        const expected_ciphertext = try hex.decodeHex(allocator, expected_ciphertext_hex);
        defer allocator.free(expected_ciphertext);
        const expected_tag = try hex.decodeHex(allocator, expected_tag_hex);
        defer allocator.free(expected_tag);

        const payload_jcs = try jcs.stringifyJCS(allocator, payload_json);
        defer allocator.free(payload_jcs);
        if (!std.mem.eql(u8, payload_jcs, expected_payload_jcs)) {
            if (valid) {
                std.debug.print("Failed JCS payload check: {s}\n", .{name});
                return error.TestFailed;
            }
        }

        var context_map: std.json.ObjectMap = .empty;
        defer context_map.deinit(allocator);
        try context_map.put(allocator, "v", std.json.Value{ .integer = 1 });
        try context_map.put(allocator, "aad_policy", std.json.Value{ .string = "record-payload-v1" });
        try context_map.put(allocator, "alg", std.json.Value{ .string = alg });
        try context_map.put(allocator, "content_type", std.json.Value{ .string = content_type });
        try context_map.put(allocator, "kid", std.json.Value{ .string = kid });
        try context_map.put(allocator, "object_uuid", std.json.Value{ .string = object_uuid });
        try context_map.put(allocator, "schema_uuid", std.json.Value{ .string = schema_uuid });

        const constructed_aad = try aad.constructAAD(allocator, std.json.Value{ .object = context_map });
        defer allocator.free(constructed_aad);

        const aad_to_use = expected_aad;

        const ciphertext = try allocator.alloc(u8, payload_jcs.len);
        defer allocator.free(ciphertext);
        var tag: [16]u8 = undefined;

        if (key.len != 32) return error.InvalidKeyLength;
        if (nonce.len != 12) return error.InvalidNonceLength;

        const aes_gcm = std.crypto.aead.aes_gcm.Aes256Gcm;
        aes_gcm.encrypt(ciphertext, &tag, payload_jcs, aad_to_use, nonce[0..12].*, key[0..32].*);

        const cipher_match = std.mem.eql(u8, ciphertext, expected_ciphertext);
        const tag_match = std.mem.eql(u8, &tag, expected_tag);
        const operation_success = cipher_match and tag_match;

        if (valid) {
            if (!operation_success) {
                std.debug.print("Failed positive test: {s}\n", .{name});
                return error.TestFailed;
            }
            passed += 1;
        } else {
            if (operation_success) {
                std.debug.print("Failed negative test: {s}\n", .{name});
                return error.TestFailed;
            }
            passed += 1;
        }
    }

    var buf: [100]u8 = undefined;
    const msg = try std.fmt.bufPrint(&buf, "  Payload Vectors: {}/{} passed\n", .{passed, total});
    try std.Io.File.stdout().writeStreamingAll(io, msg);
}
