const std = @import("std");
const jcs = @import("jcs.zig");

pub fn constructAAD(allocator: std.mem.Allocator, value: std.json.Value) ![]u8 {
    return jcs.stringifyJCS(allocator, value);
}
