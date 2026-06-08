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
                        try out.append(allocator, c);
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

fn stringLessThan(context: void, a: []const u8, b: []const u8) bool {
    _ = context;
    return std.mem.order(u8, a, b) == .lt;
}
