with open("docs/database-structure.md", "r") as f:
    content = f.read()

update_delete_notes = """
### Note on Update and Delete Operations

Initial API scaffolds for updating and deleting payloads are implemented:
*   **UpdatePayload**: Updates the payload of an existing `object_uuid`. It canonicalizes the new payload, encrypts it with a new randomly generated `nonce` reusing the existing `record_dek`, and updates the corresponding row in `encrypted_object_tbl`. `updated_at_ms` is updated, while `created_at_ms` is maintained. Key lifecycle operations (`key_tbl`, `wrapped_key_tbl`) are not altered.
*   **DeletePayload**: Performs a logical hard delete by removing the target row from `encrypted_object_tbl`.
*   **Key Lifecycle limitations**: Neither Update nor Delete perform complex key lifecycle operations such as key rotation, rewrap, or cleaning up associated `record_dek` or wrapped key materials. Secure erase guarantees and orphan key cleanup policies remain future work.
"""

content = content.replace('**Note on Lifecycle Fields**:', update_delete_notes + '\n**Note on Lifecycle Fields**:')

with open("docs/database-structure.md", "w") as f:
    f.write(content)
