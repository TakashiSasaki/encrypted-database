const std = @import("std");
const root = @import("root.zig");

pub fn main(init: std.process.Init) !void {
    try std.Io.File.stdout().writeStreamingAll(init.io, root.smokeMessage());
    try std.Io.File.stdout().writeStreamingAll(init.io, "\n");
}
