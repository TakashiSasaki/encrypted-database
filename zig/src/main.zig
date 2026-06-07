const std = @import("std");
const root = @import("root.zig");

pub fn main() !void {
    std.debug.print("{s}\n", .{root.smokeMessage()});
}
