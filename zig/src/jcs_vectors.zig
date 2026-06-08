const std = @import("std");
const json_min = @import("json_min.zig");
const jcs = @import("jcs.zig");

pub fn run(allocator: std.mem.Allocator, io: std.Io) !void {
    const vectors = try json_min.parseJsonFile(allocator, io, "test-vectors/jcs/rfc8785-basic.json");
    const arr = vectors.array;

    try std.Io.File.stdout().writeStreamingAll(io, "Running JCS canonicalization test vectors...\n");

    var passed: usize = 0;
    var total: usize = 0;

    for (arr.items) |case| {
        total += 1;
        const obj = case.object;

        const name = obj.get("name").?.string;
        const input = obj.get("input").?;
        const expected_string = obj.get("expected_string").?.string;

        const result = try jcs.stringifyJCS(allocator, input);
        defer allocator.free(result);

        if (std.mem.eql(u8, result, expected_string)) {
            passed += 1;
        } else {
            std.debug.print("Failed JCS test: {s}\nExpected: {s}\nGot:      {s}\n", .{name, expected_string, result});
            return error.TestFailed;
        }
    }

    var buf: [100]u8 = undefined;
    const msg = try std.fmt.bufPrint(&buf, "  JCS Vectors: {}/{} passed\n", .{passed, total});
    try std.Io.File.stdout().writeStreamingAll(io, msg);
}
