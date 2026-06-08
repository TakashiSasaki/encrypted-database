const std = @import("std");
const testing = std.testing;
const reader = @import("read_only_reader.zig");

test "wrong passphrase fails" {
    const allocator = testing.allocator;
    const db_path = "/tmp/test.db";
    std.fs.access(db_path, .{}) catch return;

    var alloc = std.heap.page_allocator;
    const path_z = try alloc.dupeZ(u8, db_path);
    defer alloc.free(path_z);

    const err = reader.readFixture(
        allocator,
        std.io.getStdOut().writer().any(),
        path_z,
        "wrong-passphrase",
        "c73f19cf-0e4a-40a0-8576-da5c86f0af2e",
        "0000"
    );
    try testing.expectError(reader.ReadOnlyError.KeyUnwrapFailed, err);
}

test "wrong expected hex fails" {
    const allocator = testing.allocator;
    const db_path = "/tmp/test.db";
    std.fs.access(db_path, .{}) catch return;

    var alloc = std.heap.page_allocator;
    const path_z = try alloc.dupeZ(u8, db_path);
    defer alloc.free(path_z);

    const err = reader.readFixture(
        allocator,
        std.io.getStdOut().writer().any(),
        path_z,
        "fixture-passphrase-python",
        "c73f19cf-0e4a-40a0-8576-da5c86f0af2e",
        "111111" // wrong expected hex
    );
    try testing.expectError(reader.ReadOnlyError.DecryptFailed, err);
}

test "successful read-only decrypt" {
    const allocator = testing.allocator;
    const db_path = "/tmp/test.db";
    std.fs.access(db_path, .{}) catch return;

    var alloc = std.heap.page_allocator;
    const path_z = try alloc.dupeZ(u8, db_path);
    defer alloc.free(path_z);

    const expected_hex = "7b226974656d73223a5b22707974686f6e222c22676f222c2272757374225d2c226e6573746564223a7b226f6b223a747275657d2c22736563726574223a2263726f73732d6c616e67756167652d66697874757265222c2276616c7565223a34327d";

    try reader.readFixture(
        allocator,
        std.io.getStdOut().writer().any(),
        path_z,
        "fixture-passphrase-python",
        "c73f19cf-0e4a-40a0-8576-da5c86f0af2e",
        expected_hex
    );
}
