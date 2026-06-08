const std = @import("std");

pub fn parseJsonFile(allocator: std.mem.Allocator, io: std.Io, path: []const u8) !std.json.Value {
    const cwd = std.Io.Dir.cwd();
    var file = try cwd.openFile(io, path, .{});
    defer file.close(io);

    const stat = try file.stat(io);
    const content = try allocator.alloc(u8, @intCast(stat.size));
    defer allocator.free(content);

    var bytes_read: usize = 0;
    while (bytes_read < content.len) {
        const amt = try file.readPositionalAll(io, content[bytes_read..], bytes_read);
        if (amt == 0) break;
        bytes_read += amt;
    }

    const parsed = try std.json.parseFromSlice(std.json.Value, allocator, content[0..bytes_read], .{});
    return parsed.value;
}
