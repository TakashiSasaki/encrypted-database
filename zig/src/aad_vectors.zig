const std = @import("std");
const json_min = @import("json_min.zig");
const aad = @import("aad.zig");
const hex = @import("hex.zig");

pub fn run(allocator: std.mem.Allocator, io: std.Io) !void {
    const vectors = try json_min.parseJsonFile(allocator, io, "test-vectors/aad/aad-policies-v1.json");
    const arr = vectors.array;

    try std.Io.File.stdout().writeStreamingAll(io, "Running AAD construction test vectors...\n");

    var passed: usize = 0;
    var total: usize = 0;

    for (arr.items) |case| {
        total += 1;
        const obj = case.object;

        const name = obj.get("name").?.string;
        const expected_context = obj.get("expected_context").?;
        const expected_hex = obj.get("expected_hex").?.string;

        const result_bytes = try aad.constructAAD(allocator, expected_context);
        defer allocator.free(result_bytes);

        const result_hex = try hex.encodeHex(allocator, result_bytes);
        defer allocator.free(result_hex);

        if (std.mem.eql(u8, result_hex, expected_hex)) {
            passed += 1;
        } else {
            std.debug.print("Failed AAD test: {s}\nExpected: {s}\nGot:      {s}\n", .{name, expected_hex, result_hex});
            return error.TestFailed;
        }
    }

    var buf: [100]u8 = undefined;
    const msg = try std.fmt.bufPrint(&buf, "  AAD Vectors: {}/{} passed\n", .{passed, total});
    try std.Io.File.stdout().writeStreamingAll(io, msg);
}
