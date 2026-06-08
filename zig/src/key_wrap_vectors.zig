const aad_import = @import("aad.zig");
const std = @import("std");
const json_min = @import("json_min.zig");
const hex = @import("hex.zig");

pub fn run(allocator: std.mem.Allocator, io: std.Io) !void {
    const vectors = try json_min.parseJsonFile(allocator, io, "test-vectors/key-wrap/key-wrap-v1.json");
    const arr = vectors.array;

    try std.Io.File.stdout().writeStreamingAll(io, "Running Key Wrap test vectors...\n");

    var passed: usize = 0;
    var total: usize = 0;

    for (arr.items) |case| {
        total += 1;
        const obj = case.object;

        const name = obj.get("name").?.string;
        _ = name;

        const wrapping_key_hex = obj.get("wrapping_key_hex").?.string;
        const wrapped_key_plaintext_hex = obj.get("wrapped_key_plaintext_hex").?.string;
        const nonce_hex = obj.get("nonce_hex").?.string;
        const expected_aad_hex = obj.get("expected_aad_hex").?.string;
        const expected_wrapped_key_ciphertext_hex = obj.get("expected_wrapped_key_ciphertext_hex").?.string;
        const expected_wrapped_key_tag_hex = obj.get("expected_wrapped_key_tag_hex").?.string;
        const valid = obj.get("valid").?.bool;

        const key = try hex.decodeHex(allocator, wrapping_key_hex);
        defer allocator.free(key);
        const plaintext = try hex.decodeHex(allocator, wrapped_key_plaintext_hex);
        defer allocator.free(plaintext);
        const nonce = try hex.decodeHex(allocator, nonce_hex);
        defer allocator.free(nonce);

        const aad_policy = obj.get("aad_policy").?.string;
        const wrapped_kid = obj.get("wrapped_kid").?.string;
        const wrapping_kid = obj.get("wrapping_kid").?.string;

        var context_map: std.json.ObjectMap = .empty;
        defer context_map.deinit(allocator);
        try context_map.put(allocator, "v", std.json.Value{ .integer = 1 });
        try context_map.put(allocator, "aad_policy", std.json.Value{ .string = aad_policy });
        try context_map.put(allocator, "wrapped_kid", std.json.Value{ .string = wrapped_kid });
        try context_map.put(allocator, "wrapping_kid", std.json.Value{ .string = wrapping_kid });

        const aad_bytes = try aad_import.constructAAD(allocator, std.json.Value{ .object = context_map });
        defer allocator.free(aad_bytes);

        const expected_aad = try hex.decodeHex(allocator, expected_aad_hex);
        defer allocator.free(expected_aad);

        if (!std.mem.eql(u8, aad_bytes, expected_aad)) {
             return error.TestFailed;
        }

        const expected_ciphertext = try hex.decodeHex(allocator, expected_wrapped_key_ciphertext_hex);
        defer allocator.free(expected_ciphertext);
        const expected_tag = try hex.decodeHex(allocator, expected_wrapped_key_tag_hex);
        defer allocator.free(expected_tag);

        const ciphertext = try allocator.alloc(u8, plaintext.len);
        defer allocator.free(ciphertext);
        var tag: [16]u8 = undefined;

        if (key.len != 32) return error.InvalidKeyLength;
        if (nonce.len != 12) return error.InvalidNonceLength;

        const aes_gcm = std.crypto.aead.aes_gcm.Aes256Gcm;
        aes_gcm.encrypt(ciphertext, &tag, plaintext, aad_bytes, nonce[0..12].*, key[0..32].*);

        const cipher_match = std.mem.eql(u8, ciphertext, expected_ciphertext);
        const tag_match = std.mem.eql(u8, &tag, expected_tag);
        const operation_success = cipher_match and tag_match;

        if (valid) {
            if (!operation_success) {
                return error.TestFailed;
            }
            passed += 1;
        } else {
            if (operation_success) {
                return error.TestFailed;
            }
            passed += 1;
        }
    }

    var buf: [100]u8 = undefined;
    const msg = try std.fmt.bufPrint(&buf, "  Key Wrap Vectors: {}/{} passed\n", .{passed, total});
    try std.Io.File.stdout().writeStreamingAll(io, msg);
}
