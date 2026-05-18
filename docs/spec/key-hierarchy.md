# Key Hierarchy

This specification employs a hierarchical key model to separate access control, wrapping mechanisms, and data encryption.

## Key Classes

The following key classes are used:

| `key_class` | Meaning |
|---|---|
| `unlock_kek` | The top-level Key Encryption Key (KEK). It is obtained from sources like passphrase KDF, OS secret store, Shamir recovery, hardware tokens, etc. |
| `database_kek` | A KEK corresponding to a single database or vault. It is used to wrap `record_dek` or `file_dek`s. |
| `workspace_kek` | An optional intermediate KEK used for sharing boundaries like workspaces, collections, or projects. |
| `record_dek` | A Data Encryption Key (DEK) used to encrypt a single logical record, JSON object, or secret item. |
| `file_dek` | A DEK used to encrypt attachments, large BLOBs, or external files. |
| `index_key` | A key used for keyed blind indexes, HMAC-based search indexes, or duplicate detection keyed digests. |

## Hierarchy Structure

1. **Top Level (`unlock_kek`):** The hierarchy is entered via one or more `unlock_kek`s.
2. **Intermediate Level (`database_kek`):** The `unlock_kek` is used to unwrap the `database_kek`. Because multiple `unlock_kek`s can wrap the same `database_kek`, the system supports multiple unlock pathways (e.g., password + biometric).
3. **Optional Grouping (`workspace_kek`):** If sharing or logical boundaries are needed, a `database_kek` can wrap a `workspace_kek`.
4. **Data Level (`record_dek`, `file_dek`):** These keys encrypt the actual payload or file content. They are wrapped by a `database_kek` (or `workspace_kek`).
