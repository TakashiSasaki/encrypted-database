const std = @import("std");
const root = @import("root.zig");
const validator = @import("validator.zig");

pub fn main(init: std.process.Init) !void {
    var iter = init.minimal.args.iterate();

    // Skip executable name
    _ = iter.next();

    const cmd = iter.next();
    if (cmd == null) {
        // No arguments - smoke test behavior
        try std.Io.File.stdout().writeStreamingAll(init.io, root.smokeMessage());
        try std.Io.File.stdout().writeStreamingAll(init.io, "\n");
        return;
    }

    if (std.mem.eql(u8, cmd.?, "validate")) {
        const path = iter.next();
        if (path == null) {
            std.debug.print("Usage: vault-zig-smoke-test validate <path-to-sqlite-v1-db>\n", .{});
            std.process.exit(1);
        }

        // We need a null-terminated string for C ABI
        var alloc = std.heap.page_allocator;
        const path_z = try alloc.dupeZ(u8, path.?);
        defer alloc.free(path_z);

        validator.validateReadOnly(path_z) catch |err| {
            std.debug.print("Validation failed: {}\n", .{err});
            std.process.exit(1);
        };
        try std.Io.File.stdout().writeStreamingAll(init.io, "Validation successful.\n");
        return;
    }

    std.debug.print("Unknown command. Usage:\n", .{});
    std.debug.print("  (no args) : Run smoke test\n", .{});
    std.debug.print("  validate <path> : Validate an existing SQLite V1 database\n", .{});
    std.process.exit(1);
}
