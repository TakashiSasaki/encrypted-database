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

    if (std.mem.eql(u8, cmd.?, "read")) {
        const path = iter.next();
        const passphrase = iter.next();
        const object_uuid = iter.next();

        if (path == null or passphrase == null or object_uuid == null) {
            std.debug.print("Usage: vault-zig-smoke-test read <path-to-sqlite-v1-db> <passphrase> <object-uuid>\n", .{});
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

        var result = root.read_only_reader.readObject(alloc, init.io, path_z, passphrase.?, object_uuid.?) catch |err| {
            std.debug.print("Read failed: {}\n", .{err});
            std.process.exit(1);
        };
        defer result.deinit(alloc);

        try std.Io.File.stdout().writeStreamingAll(init.io, result.payload);
        return;
    }

    if (std.mem.eql(u8, cmd.?, "write-matrix")) {
        const db_path_opt = iter.next();
        const passphrase_opt = iter.next();
        const platform_opt = iter.next();
        const schema_uuid_opt = iter.next();
        const content_type_opt = iter.next();
        const payload_a_opt = iter.next();
        const payload_b_opt = iter.next();
        const mode_opt = iter.next();

        if (db_path_opt == null or passphrase_opt == null or platform_opt == null or schema_uuid_opt == null or content_type_opt == null or payload_a_opt == null or payload_b_opt == null) {
            std.debug.print("Usage: vault-zig-smoke-test write-matrix <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a> <payload_b> [mode]\n", .{});
            std.process.exit(1);
        }

        const mode = if (mode_opt) |m| m else "update_delete";
        if (!std.mem.eql(u8, mode, "update_only") and !std.mem.eql(u8, mode, "update_delete")) {
            std.debug.print("invalid mode: {s}\n", .{mode});
            std.process.exit(1);
        }

        var alloc = std.heap.page_allocator;
        const db_path_z = alloc.dupeZ(u8, db_path_opt.?) catch unreachable;
        defer alloc.free(db_path_z);

        var my_writer = root.writer.createNew(alloc, init.io, db_path_z, passphrase_opt.?, platform_opt.?) catch |err| {
            std.debug.print("create DB error: {}\n", .{err});
            std.process.exit(1);
        };
        defer my_writer.close();

        const object_uuid = my_writer.storePayload(init.io, schema_uuid_opt.?, content_type_opt.?, payload_a_opt.?) catch |err| {
            std.debug.print("store error: {}\n", .{err});
            std.process.exit(1);
        };

        my_writer.updatePayload(init.io, object_uuid, schema_uuid_opt.?, content_type_opt.?, payload_b_opt.?) catch |err| {
            std.debug.print("update error: {}\n", .{err});
            std.process.exit(1);
        };

        var deleted = false;
        if (std.mem.eql(u8, mode, "update_delete")) {
            my_writer.deletePayload(object_uuid) catch |err| {
                std.debug.print("delete error: {}\n", .{err});
                std.process.exit(1);
            };
            deleted = true;
        }

        // Canonicalize
        const jcs_import = @import("jcs.zig");
        var parsed_a = std.json.parseFromSlice(std.json.Value, alloc, payload_a_opt.?, .{}) catch |err| {
            std.debug.print("canonicalize A error: {}\n", .{err});
            std.process.exit(1);
        };
        defer parsed_a.deinit();
        const initial_jcs = jcs_import.stringifyJCS(alloc, parsed_a.value) catch |err| {
            std.debug.print("canonicalize A error: {}\n", .{err});
            std.process.exit(1);
        };
        defer alloc.free(initial_jcs);

        var parsed_b = std.json.parseFromSlice(std.json.Value, alloc, payload_b_opt.?, .{}) catch |err| {
            std.debug.print("canonicalize B error: {}\n", .{err});
            std.process.exit(1);
        };
        defer parsed_b.deinit();
        const updated_jcs = jcs_import.stringifyJCS(alloc, parsed_b.value) catch |err| {
            std.debug.print("canonicalize B error: {}\n", .{err});
            std.process.exit(1);
        };
        defer alloc.free(updated_jcs);

        const hex_import = @import("hex.zig");
        const initial_hex = hex_import.encodeHex(alloc, initial_jcs) catch unreachable;
        defer alloc.free(initial_hex);
        const updated_hex = hex_import.encodeHex(alloc, updated_jcs) catch unreachable;
        defer alloc.free(updated_hex);

        const out_fmt =
            \\{{"object_uuid":"{s}","initial_payload_hex":"{s}","updated_payload_hex":"{s}","deleted":{}}}
            \\
        ;

        var out_buf: [1024]u8 = undefined;
        const out_str = std.fmt.bufPrint(&out_buf, out_fmt, .{ object_uuid, initial_hex, updated_hex, deleted }) catch unreachable;

        std.Io.File.stdout().writeStreamingAll(init.io, out_str) catch |err| {
            std.debug.print("output encode error: {}\n", .{err});
            std.process.exit(1);
        };
        alloc.free(object_uuid);
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
    std.debug.print("  read <path> <passphrase> <object-uuid> : Read and decrypt a payload to stdout\n", .{});
    std.debug.print("  read-fixture <path> <passphrase> <object-uuid> <expected-hex> : Validate reading and decrypting a fixture payload\n", .{});
    std.debug.print("  write-matrix <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a> <payload_b> [mode] : Write matrix tests\n", .{});
    std.process.exit(1);
}
