# Argon2id Default Parameters

For deriving `unlock_kek` from user passwords, the library relies on the Argon2id KDF.
To ensure standard robustness and resistance to various attacks (such as dictionary, brute-force, and side-channel attacks), the following default parameters have been chosen:

| Parameter   | Value   | Description |
| ----------- | ------- | ----------- |
| Time Cost   | 3       | The number of iterations. Provides a baseline of processing time. |
| Memory Cost | 65536   | The memory consumption in KiB (64 MiB). Provides a practical compromise that works cross-platform including in browser WebAssembly environments. |
| Parallelism | 1       | The number of independent computational threads. Set to 1 for reliable cross-platform execution (especially WebAssembly). |
| Salt Length | 16      | The size of the random salt in bytes. Ensures unique hashes per user. |
| Output Size | 32      | The size of the derived key in bytes. |

These parameters (Profile V1) are platform-independent. The library uses the exact same `memory_kib=65536`, `iterations=3`, `parallelism=1`, `salt_bytes=16`, and `output_bytes=32` when initializing new databases across Python, Node.js, and browser environments. We do not introduce adaptive or platform-specific profiles at this time.
Existing databases will continue to unlock using the provider configuration (salt, memory_kib, iterations, parallelism) saved in their `provider_config_json`, ensuring backward compatibility with previously utilized parameters.
