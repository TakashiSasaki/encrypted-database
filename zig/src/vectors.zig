const std = @import("std");
const aead_vectors = @import("aead_vectors.zig");
const kdf_vectors = @import("kdf_vectors.zig");
const key_wrap_vectors = @import("key_wrap_vectors.zig");
const jcs_vectors = @import("jcs_vectors.zig");
const aad_vectors = @import("aad_vectors.zig");
const payload_vectors = @import("payload_vectors.zig");

pub fn main(init: std.process.Init) !void {
    var arena = std.heap.ArenaAllocator.init(std.heap.page_allocator);
    defer arena.deinit();
    const allocator = arena.allocator();

    try std.Io.File.stdout().writeStreamingAll(init.io, "Running Zig shared-vector conformance suite...\n");

    try aead_vectors.run(allocator, init.io);
    try kdf_vectors.run(allocator, init.io);
    try key_wrap_vectors.run(allocator, init.io);
    try jcs_vectors.run(allocator, init.io);
    try aad_vectors.run(allocator, init.io);
    try payload_vectors.run(allocator, init.io);

    try std.Io.File.stdout().writeStreamingAll(init.io, "All selected vectors passed.\n");
}
