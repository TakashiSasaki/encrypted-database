const std = @import("std");
const json_min = @import("json_min.zig");
const hex = @import("hex.zig");

pub fn run(allocator: std.mem.Allocator, io: std.Io) !void {
    const vectors = try json_min.parseJsonFile(allocator, io, "test-vectors/aead/aes-256-gcm-v1.json");
    const arr = vectors.array;

    try std.Io.File.stdout().writeStreamingAll(io, "Running AEAD AES-256-GCM test vectors...\n");

    var passed: usize = 0;
    var total: usize = 0;

    for (arr.items) |case| {
        total += 1;
        const obj = case.object;

        const name = obj.get("name").?.string;
        const key_hex = obj.get("key_hex").?.string;
        const nonce_hex = obj.get("nonce_hex").?.string;
        const aad_hex = obj.get("aad_hex").?.string;
        const plaintext_hex = obj.get("plaintext_hex").?.string;
        const expected_ciphertext_hex = obj.get("expected_ciphertext_hex").?.string;
        const expected_tag_hex = obj.get("expected_tag_hex").?.string;
        const valid = obj.get("valid").?.bool;

        const key = try hex.decodeHex(allocator, key_hex);
        defer allocator.free(key);
        const nonce = try hex.decodeHex(allocator, nonce_hex);
        defer allocator.free(nonce);
        const aad = try hex.decodeHex(allocator, aad_hex);
        defer allocator.free(aad);
        const plaintext = try hex.decodeHex(allocator, plaintext_hex);
        defer allocator.free(plaintext);
        const expected_ciphertext = try hex.decodeHex(allocator, expected_ciphertext_hex);
        defer allocator.free(expected_ciphertext);
        const expected_tag = try hex.decodeHex(allocator, expected_tag_hex);
        defer allocator.free(expected_tag);

        const ciphertext = try allocator.alloc(u8, plaintext.len);
        defer allocator.free(ciphertext);
        var tag: [16]u8 = undefined;

        if (key.len != 32) return error.InvalidKeyLength;
        if (nonce.len != 12) return error.InvalidNonceLength;

        const aes_gcm = std.crypto.aead.aes_gcm.Aes256Gcm;

        var operation_success = true;
        if (valid) {
            aes_gcm.encrypt(ciphertext, &tag, plaintext, aad, nonce[0..12].*, key[0..32].*);
            const cipher_match = std.mem.eql(u8, ciphertext, expected_ciphertext);
            const tag_match = std.mem.eql(u8, &tag, expected_tag);
            operation_success = cipher_match and tag_match;
        } else {
            // Negative tests are decryption authentication failures, must decrypt.
            const out_plaintext = try allocator.alloc(u8, expected_ciphertext.len);
            defer allocator.free(out_plaintext);

            aes_gcm.decrypt(out_plaintext, expected_ciphertext, expected_tag[0..16].*, aad, nonce[0..12].*, key[0..32].*) catch {
                operation_success = false;
            };
        }

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
    const msg = try std.fmt.bufPrint(&buf, "  AEAD Vectors: {}/{} passed\n", .{passed, total});
    try std.Io.File.stdout().writeStreamingAll(io, msg);
}
