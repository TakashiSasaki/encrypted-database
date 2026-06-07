const std = @import("std");

pub fn smokeMessage() []const u8 {
    return "vault zig smoke test ok";
}

test "smokeMessage returns expected string" {
    try std.testing.expectEqualStrings("vault zig smoke test ok", smokeMessage());
}
