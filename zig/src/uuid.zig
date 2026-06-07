const std = @import("std");

pub const UuidError = error{
    InvalidLength,
    InvalidChar,
    InvalidHyphen,
    InvalidVersion,
    InvalidVariant,
};

pub fn validateCanonical(uuid: []const u8) UuidError!void {
    if (uuid.len != 36) {
        return UuidError.InvalidLength;
    }

    // Pattern: ^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$
    const hyphen_indices = [_]usize{ 8, 13, 18, 23 };

    for (uuid, 0..) |char, i| {
        if (i == hyphen_indices[0] or i == hyphen_indices[1] or i == hyphen_indices[2] or i == hyphen_indices[3]) {
            if (char != '-') return UuidError.InvalidHyphen;
            continue;
        }

        if (i == 14) { // Version character [1-8]
            if (char < '1' or char > '8') return UuidError.InvalidVersion;
            continue;
        }

        if (i == 19) { // Variant character [89ab]
            if (char != '8' and char != '9' and char != 'a' and char != 'b') return UuidError.InvalidVariant;
            continue;
        }

        // [0-9a-f]
        if (!((char >= '0' and char <= '9') or (char >= 'a' and char <= 'f'))) {
            return UuidError.InvalidChar;
        }
    }
}
