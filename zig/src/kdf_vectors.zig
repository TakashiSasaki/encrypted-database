const std = @import("std");
const json_min = @import("json_min.zig");
const hex = @import("hex.zig");

pub fn run(allocator: std.mem.Allocator, io: std.Io) !void {
    const vectors = try json_min.parseJsonFile(allocator, io, "test-vectors/kdf/argon2id-v1.json");
    const arr = vectors.array;

    try std.Io.File.stdout().writeStreamingAll(io, "Running KDF Argon2id test vectors...\n");

    var passed: usize = 0;
    var total: usize = 0;

    for (arr.items) |case| {
        total += 1;
        const obj = case.object;

        const profile = obj.get("profile").?.string;
        _ = profile;

        const input = obj.get("input").?.object;
        const passphrase = input.get("passphrase").?.string;
        const salt_hex = input.get("salt_hex").?.string;

        const params = obj.get("parameters").?.object;
        const memory_kib = params.get("memory_kib").?.integer;
        const iterations = params.get("iterations").?.integer;
        const parallelism = params.get("parallelism").?.integer;

        const expected_output_hex = obj.get("expected_output_hex").?.string;

        const salt = try hex.decodeHex(allocator, salt_hex);
        defer allocator.free(salt);
        const expected_output = try hex.decodeHex(allocator, expected_output_hex);
        defer allocator.free(expected_output);

        const output = try allocator.alloc(u8, expected_output.len);
        defer allocator.free(output);

        const argon2 = std.crypto.pwhash.argon2;

        const t_cost: u32 = @intCast(iterations);
        const m_cost: u32 = @intCast(memory_kib);
        const p_cost: u24 = @intCast(parallelism);

        try argon2.kdf(allocator, output, passphrase, salt, .{
            .t = t_cost,
            .m = m_cost,
            .p = p_cost,
        }, .argon2id, io);

        if (std.mem.eql(u8, output, expected_output)) {
            passed += 1;
        } else {
            std.debug.print("Failed KDF test\n", .{});
            return error.TestFailed;
        }
    }

    var buf: [100]u8 = undefined;
    const msg = try std.fmt.bufPrint(&buf, "  KDF Vectors: {}/{} passed\n", .{passed, total});
    try std.Io.File.stdout().writeStreamingAll(io, msg);
}
