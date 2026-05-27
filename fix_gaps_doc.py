with open("docs/implementation-notes/implementation-gaps.md", "r") as f:
    content = f.read()

content = content.replace(
    "- Go/Rust writer scaffolds only support `CreateNew` and `StorePayload`.",
    "- Go/Rust writer scaffolds support `CreateNew`, `StorePayload`, `UpdatePayload`, and `DeletePayload`."
)

key_lifecycle_notes = """
### Key Lifecycle and Cleanup

Complex key lifecycle features are intentionally omitted from the current `UpdatePayload` and `DeletePayload` operations. Currently:
*   `UpdatePayload` reuses the existing `record_dek` without generating a new key or performing any rewrap operation.
*   `DeletePayload` performs a logical hard delete by removing the row in `encrypted_object_tbl` but leaves behind the associated `record_dek` and `wrapped_key_tbl` records (orphan keys).
*   Key cleanup policies and secure erase guarantees are not implemented and remain future work.
"""

content = content.replace('## Storage Format V1 Baselines', key_lifecycle_notes + '\n## Storage Format V1 Baselines')

with open("docs/implementation-notes/implementation-gaps.md", "w") as f:
    f.write(content)
