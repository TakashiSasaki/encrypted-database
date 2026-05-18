# SQLite Constraints and Enforcement

The SQLite implementation relies heavily on constraints to maintain the integrity of the cryptographic relationships and versioning data.

## Foreign Key Enforcement

SQLite does not enforce Foreign Keys by default. Applications must explicitly enable them immediately upon opening a connection.

```sql
PRAGMA foreign_keys = ON;
```

If this PRAGMA is not executed, the library might silently allow invalid data states, such as orphaned wrapped keys, references to non-existent platform strings, or missing `key_tbl` entries. In Node.js environments (using `better-sqlite3`), this should be executed synchronously before any transactions begin.

## Version and Type Enforcement

To ensure backward compatibility and clear migration paths, the storage format is explicitly versioned within the schema via table constraints.

### `encrypted_object_tbl` Constraints

```sql
envelope_v INTEGER NOT NULL DEFAULT 1 CHECK (envelope_v >= 1),
envelope_type TEXT NOT NULL DEFAULT 'aead' CHECK (envelope_type IN ('aead'))
```

### `wrapped_key_tbl` Constraints

```sql
envelope_v INTEGER NOT NULL DEFAULT 1 CHECK (envelope_v >= 1),
envelope_type TEXT NOT NULL DEFAULT 'key_wrap' CHECK (envelope_type IN ('key_wrap'))
```

These explicit `CHECK` constraints prevent applications from accidentally inserting unversioned payloads or incompatible envelope types into the database. If new formats are supported in the future, the `CHECK` constraints must be explicitly migrated.
