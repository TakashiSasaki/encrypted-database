const std = @import("std");
const c = @cImport({
    @cInclude("sqlite3.h");
});

pub const SQLiteError = error{
    OpenFailed,
    PrepareFailed,
    StepFailed,
    QueryFailed,
};

pub const Database = struct {
    db: *c.sqlite3,

    pub fn openReadOnly(path: [:0]const u8) !Database {
        var db: ?*c.sqlite3 = null;
        const flags = c.SQLITE_OPEN_READONLY | c.SQLITE_OPEN_URI;
        const rc = c.sqlite3_open_v2(path.ptr, &db, flags, null);
        if (rc != c.SQLITE_OK) {
            if (db) |d| {
                _ = c.sqlite3_close(d);
            }
            return SQLiteError.OpenFailed;
        }
        return Database{ .db = db.? };
    }

    pub fn close(self: *Database) void {
        _ = c.sqlite3_close(self.db);
    }

    pub fn exec(self: *Database, sql: [:0]const u8) !void {
        var err_msg: [*c]u8 = null;
        const rc = c.sqlite3_exec(self.db, sql.ptr, null, null, &err_msg);
        if (rc != c.SQLITE_OK) {
            if (err_msg != null) {
                c.sqlite3_free(err_msg);
            }
            return SQLiteError.QueryFailed;
        }
    }

    pub fn queryPragmaInt(self: *Database, pragma_sql: [:0]const u8) !i64 {
        var stmt: ?*c.sqlite3_stmt = null;
        var rc = c.sqlite3_prepare_v2(self.db, pragma_sql.ptr, -1, &stmt, null);
        if (rc != c.SQLITE_OK) {
            return SQLiteError.PrepareFailed;
        }
        defer _ = c.sqlite3_finalize(stmt);

        rc = c.sqlite3_step(stmt);
        if (rc == c.SQLITE_ROW) {
            return c.sqlite3_column_int64(stmt, 0);
        }
        return SQLiteError.StepFailed;
    }

    pub fn checkTableExists(self: *Database, table_name: [:0]const u8) !bool {
        const sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=?";
        var stmt: ?*c.sqlite3_stmt = null;
        var rc = c.sqlite3_prepare_v2(self.db, sql, -1, &stmt, null);
        if (rc != c.SQLITE_OK) {
            return SQLiteError.PrepareFailed;
        }
        defer _ = c.sqlite3_finalize(stmt);

        rc = c.sqlite3_bind_text(stmt, 1, table_name.ptr, -1, c.SQLITE_STATIC);
        if (rc != c.SQLITE_OK) {
            return SQLiteError.StepFailed;
        }

        rc = c.sqlite3_step(stmt);
        if (rc == c.SQLITE_ROW) {
            return true;
        } else if (rc == c.SQLITE_DONE) {
            return false;
        }
        return SQLiteError.StepFailed;
    }
};

pub const Statement = struct {
    stmt: *c.sqlite3_stmt,

    pub fn prepare(db: *Database, sql: [:0]const u8) !Statement {
        var stmt: ?*c.sqlite3_stmt = null;
        const rc = c.sqlite3_prepare_v2(db.db, sql.ptr, -1, &stmt, null);
        if (rc != c.SQLITE_OK) {
            return SQLiteError.PrepareFailed;
        }
        return Statement{ .stmt = stmt.? };
    }

    pub fn finalize(self: *Statement) void {
        _ = c.sqlite3_finalize(self.stmt);
    }

    pub fn step(self: *Statement) !bool {
        const rc = c.sqlite3_step(self.stmt);
        if (rc == c.SQLITE_ROW) {
            return true;
        } else if (rc == c.SQLITE_DONE) {
            return false;
        }
        return SQLiteError.StepFailed;
    }

    pub fn columnText(self: *Statement, col: i32) ?[]const u8 {
        const text_ptr = c.sqlite3_column_text(self.stmt, col);
        if (text_ptr == null) {
            return null;
        }
        const len = c.sqlite3_column_bytes(self.stmt, col);
        if (len < 0) {
            return null;
        }
        return text_ptr[0..@intCast(len)];
    }

    pub fn columnBlob(self: *Statement, col: i32) ?[]const u8 {
        const blob_ptr = c.sqlite3_column_blob(self.stmt, col);
        if (blob_ptr == null) {
            return null;
        }
        const len = c.sqlite3_column_bytes(self.stmt, col);
        if (len < 0) {
            return null;
        }
        const byte_ptr: [*]const u8 = @ptrCast(blob_ptr);
        return byte_ptr[0..@intCast(len)];
    }

    pub fn columnInt64(self: *Statement, col: i32) i64 {
        return c.sqlite3_column_int64(self.stmt, col);
    }

    pub fn bindText(self: *Statement, col: i32, text: []const u8) !void {
        const rc = c.sqlite3_bind_text(self.stmt, col, text.ptr, @intCast(text.len), c.SQLITE_TRANSIENT);
        if (rc != c.SQLITE_OK) {
            return SQLiteError.StepFailed;
        }
    }

    pub fn reset(self: *Statement) !void {
        const rc = c.sqlite3_reset(self.stmt);
        if (rc != c.SQLITE_OK) {
            return SQLiteError.StepFailed;
        }
        _ = c.sqlite3_clear_bindings(self.stmt);
    }
};
