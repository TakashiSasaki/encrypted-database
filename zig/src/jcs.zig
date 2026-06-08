const std = @import("std");

pub fn stringifyJCS(allocator: std.mem.Allocator, value: std.json.Value) ![]u8 {
    var out = std.ArrayList(u8).initCapacity(allocator, 1024) catch unreachable;
    errdefer out.deinit(allocator);
    try serializeValue(&out, allocator, value);
    return try out.toOwnedSlice(allocator);
}

fn serializeValue(out: *std.ArrayList(u8), allocator: std.mem.Allocator, value: std.json.Value) !void {
    switch (value) {
        .null => try out.appendSlice(allocator, "null"),
        .bool => |b| if (b) try out.appendSlice(allocator, "true") else try out.appendSlice(allocator, "false"),
        .integer => |i| {
            var buf: [128]u8 = undefined;
            const s = try std.fmt.bufPrint(&buf, "{d}", .{i});
            try out.appendSlice(allocator, s);
        },
        .float => |f| {
            var buf: [128]u8 = undefined;
            const s = try std.fmt.bufPrint(&buf, "{d}", .{f});
            try out.appendSlice(allocator, s);
        },
        .string => |s| {
            try out.append(allocator, '"');
            for (s) |c| {
                switch (c) {
                    '"' => try out.appendSlice(allocator, "\\\""),
                    '\\' => try out.appendSlice(allocator, "\\\\"),
                    '\x08' => try out.appendSlice(allocator, "\\b"),
                    '\x0C' => try out.appendSlice(allocator, "\\f"),
                    '\n' => try out.appendSlice(allocator, "\\n"),
                    '\r' => try out.appendSlice(allocator, "\\r"),
                    '\t' => try out.appendSlice(allocator, "\\t"),
                    else => {
                        if (c < 0x20) {
                            var buf: [6]u8 = undefined;
                            const esc = try std.fmt.bufPrint(&buf, "\\u00{x:0>2}", .{c});
                            try out.appendSlice(allocator, esc);
                        } else {
                            try out.append(allocator, c);
                        }
                    }
                }
            }
            try out.append(allocator, '"');
        },
        .array => |arr| {
            try out.append(allocator, '[');
            for (arr.items, 0..) |item, i| {
                if (i > 0) try out.append(allocator, ',');
                try serializeValue(out, allocator, item);
            }
            try out.append(allocator, ']');
        },
        .object => |obj| {
            try out.append(allocator, '{');

            var keys = try allocator.alloc([]const u8, obj.count());
            defer allocator.free(keys);

            var i: usize = 0;
            var it = obj.iterator();
            while (it.next()) |entry| {
                keys[i] = entry.key_ptr.*;
                i += 1;
            }

            std.mem.sort([]const u8, keys, {}, stringLessThan);

            for (keys, 0..) |key, idx| {
                if (idx > 0) try out.append(allocator, ',');

                try serializeValue(out, allocator, std.json.Value{ .string = key });

                try out.append(allocator, ':');
                try serializeValue(out, allocator, obj.get(key).?);
            }
            try out.append(allocator, '}');
        },
        else => return error.UnsupportedJsonType,
    }
}

fn nextUtf16CodeUnit(utf8: []const u8, index: *usize, pending_low_surrogate: *?u16) ?u16 {
    if (pending_low_surrogate.*) |low| {
        pending_low_surrogate.* = null;
        return low;
    }
    if (index.* >= utf8.len) return null;

    const cp_len = std.unicode.utf8ByteSequenceLength(utf8[index.*]) catch 1;
    if (index.* + cp_len > utf8.len) {
        const b = utf8[index.*];
        index.* += 1;
        return @as(u16, b);
    }

    const cp = std.unicode.utf8Decode(utf8[index.* .. index.* + cp_len]) catch {
        const b = utf8[index.*];
        index.* += 1;
        return @as(u16, b);
    };

    index.* += cp_len;

    if (cp <= 0xFFFF) {
        return @as(u16, @intCast(cp));
    } else {
        const high = 0xD800 + @as(u16, @intCast((cp - 0x10000) >> 10));
        const low = 0xDC00 + @as(u16, @intCast((cp - 0x10000) & 0x3FF));
        pending_low_surrogate.* = low;
        return high;
    }
}

fn stringLessThan(context: void, a: []const u8, b: []const u8) bool {
    _ = context;
    var idx_a: usize = 0;
    var idx_b: usize = 0;
    var pend_a: ?u16 = null;
    var pend_b: ?u16 = null;

    while (true) {
        const cu_a = nextUtf16CodeUnit(a, &idx_a, &pend_a);
        const cu_b = nextUtf16CodeUnit(b, &idx_b, &pend_b);

        if (cu_a == null and cu_b == null) return false;
        if (cu_a == null) return true;
        if (cu_b == null) return false;

        if (cu_a.? < cu_b.?) return true;
        if (cu_a.? > cu_b.?) return false;
    }
}
