# Search and Blind Indexes

Because payloads are stored as AEAD-encrypted envelopes, full-text search directly on the database via standard SQL `LIKE` or `MATCH` queries on plaintext content is not possible.

If an application requires searching on specific encrypted fields (e.g., email addresses, specific tags, or usernames) while maintaining privacy against an offline database observer, it must use Blind Indexes.

## Index Keys

A specific key of class `index_key` must be generated and stored similarly to a `database_kek` or `workspace_kek`.

- **key_class:** `index_key`
- **purpose:** `blind_index`
- **alg:** `HMAC-SHA256` (or another appropriate MAC algorithm).

## Generating Blind Index Entries

1. Extract the field to be indexed from the plaintext JSON payload.
2. If the field is a string, it must be appropriately normalized (e.g., lowercased, stripped of whitespace) depending on the search requirements. If it's a JSON structure, it must be canonicalized.
3. Compute the HMAC of the normalized field value using the `index_key`.
4. Truncate or encode the resulting HMAC output to be stored in an indexing table.

## Storing and Querying

The HMAC output can be stored in a separate table alongside the `object_uuid`.

When a user searches for a term:
1. The application normalizes the search term identically to the indexing step.
2. The application computes the HMAC using the active `index_key` held in memory.
3. The application issues a SQL query to find exact matches of the computed HMAC against the blind index table.
4. The application retrieves the corresponding `object_uuid`s and decrypts their payloads.

**Security Consideration:** Blind indexes leak the fact that two records have identical values for the indexed field (frequency analysis). They should be used sparingly and only on fields where this leakage is acceptable within the threat model.
