import os

files = ["go/README.md", "rust/README.md"]
for file in files:
    with open(file, "r") as f:
        content = f.read()

    content = content.replace("- Store Payload (initial insertion)", "- Store Payload (initial insertion)\n- Update Payload\n- Delete Payload (logical hard delete of payload only)")
    content = content.replace("- Key Rotation", "- Key Lifecycle, Key Rotation, Rewrap, and Orphan Key Cleanup Policy")
    content = content.replace("- Secure Erase Guarantee", "- Secure Erase Guarantee")

    with open(file, "w") as f:
        f.write(content)

with open("integration-tests/write-matrix/README.md", "r") as f:
    content = f.read()

content = content.replace(
    "- Go/Rust Write DB -> Node.js/Python Read DB",
    "- Go/Rust Write/Update/Delete DB -> Node.js/Python Read/Verify DB"
)

content = content.replace(
    "It acts as a lightweight functional check",
    "It acts as a lightweight functional check. The tests orchestrate `store`, `update`, and `delete` scenarios. Note that `delete` performs a logical hard delete on the payload row without secure erase guarantees or key cleanup."
)

with open("integration-tests/write-matrix/README.md", "w") as f:
    f.write(content)
