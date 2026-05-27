with open("docs/implementation-notes/writer-field-mapping.md", "r") as f:
    content = f.read()

update_delete_mapping = """

## Update and Delete Handling

The initial update and delete APIs handle fields as follows:

*   **UpdatePayload**:
    *   `encrypted_object_tbl.nonce`: A new 12-byte crypto-secure random nonce is generated.
    *   `encrypted_object_tbl.ciphertext`: Updated with the AES-256-GCM encryption of the new canonical JCS payload.
    *   `encrypted_object_tbl.updated_at_ms`: Updated to the current epoch time.
    *   `encrypted_object_tbl.created_at_ms`: Maintained as the original creation time.
    *   `encrypted_object_tbl.schema_uuid` / `content_type`: Can be updated via API parameters.
    *   `key_tbl` / `wrapped_key_tbl`: Maintained (no changes, existing `record_dek` is reused).
*   **DeletePayload**:
    *   The corresponding row in `encrypted_object_tbl` is completely deleted.
    *   `key_tbl` / `wrapped_key_tbl`: Maintained (no cleanup of `record_dek` or its wrapped variants is performed currently).
"""

content = content + update_delete_mapping

with open("docs/implementation-notes/writer-field-mapping.md", "w") as f:
    f.write(content)
