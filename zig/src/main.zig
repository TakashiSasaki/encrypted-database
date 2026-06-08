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

    if (std.mem.eql(u8, cmd.?, "read-fixture")) {
        const path = iter.next();
        const passphrase = iter.next();
        const object_uuid = iter.next();
        const expected_hex = iter.next();

        if (path == null or passphrase == null or object_uuid == null or expected_hex == null) {
            std.debug.print("Usage: vault-zig-smoke-test read-fixture <path-to-sqlite-v1-db> <passphrase> <object-uuid> <expected-hex>\n", .{});
            std.process.exit(1);
        }

        var alloc = std.heap.page_allocator;
        const path_z = try alloc.dupeZ(u8, path.?);
        defer alloc.free(path_z);

        // Run validation first
        validator.validateReadOnly(path_z) catch |err| {
            std.debug.print("Validation failed: {}\n", .{err});
            std.process.exit(1);
        };

        root.read_only_reader.readFixture(alloc, init.io, path_z, passphrase.?, object_uuid.?, expected_hex.?) catch |err| {
            std.debug.print("Read fixture failed: {}\n", .{err});
            std.process.exit(1);
        };

        try std.Io.File.stdout().writeStreamingAll(init.io, "Read fixture successful.\n");
        return;
    }

    std.debug.print("Unknown command. Usage:\n", .{});
    std.debug.print("  (no args) : Run smoke test\n", .{});
    std.debug.print("  validate <path> : Validate an existing SQLite V1 database\n", .{});
    std.debug.print("  read-fixture <path> <passphrase> <object-uuid> <expected-hex> : Validate reading and decrypting a fixture payload\n", .{});
    std.process.exit(1);
}
