with open("integration-tests/write-matrix/README.md", "r") as f:
    content = f.read()

content = content.replace("It verifies that databases created and populated by the Go/Rust writer scaffolds can be successfully unlocked and the payloads correctly decrypted by all baseline language implementations.", "It verifies that databases created, updated, and deleted by the Go/Rust writer scaffolds can be successfully unlocked and the payloads correctly decrypted (or NotFound verified) by baseline language implementations. The tests orchestrate `store`, `update`, and `delete` scenarios. Note that `delete` performs a logical hard delete on the payload row without secure erase guarantees or key cleanup.")

content = content.replace("(features like update, delete, and key lifecycle are intentionally absent)", "(key lifecycle, key rotation, and secure erase are intentionally absent)")

with open("integration-tests/write-matrix/README.md", "w") as f:
    f.write(content)
