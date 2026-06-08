const std = @import("std");

pub fn decodeHex(allocator: std.mem.Allocator, hex: []const u8) ![]u8 {
    const len = hex.len / 2;
    const out = try allocator.alloc(u8, len);
    errdefer allocator.free(out);
    _ = try std.fmt.hexToBytes(out, hex);
    return out;
}

pub fn encodeHex(allocator: std.mem.Allocator, bytes: []const u8) ![]u8 {
    const out = try allocator.alloc(u8, bytes.len * 2);
    errdefer allocator.free(out);
    const alphabet = "0123456789abcdef";
    for (bytes, 0..) |b, i| {
        out[i * 2] = alphabet[b >> 4];
        out[i * 2 + 1] = alphabet[b & 0x0F];
    }
    return out;
}
