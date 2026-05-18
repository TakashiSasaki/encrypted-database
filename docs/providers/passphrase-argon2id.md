# Argon2id Default Parameters

For deriving `unlock_kek` from user passwords, the library relies on the Argon2id KDF.
To ensure standard robustness and resistance to various attacks (such as dictionary, brute-force, and side-channel attacks), the following default parameters have been chosen:

| Parameter   | Value   | Description |
| ----------- | ------- | ----------- |
| Time Cost   | 3       | The number of iterations. Provides a baseline of processing time. |
| Memory Cost | 262144  | The memory consumption in KiB (256 MB). Defends against hardware-optimized cracking using GPUs/ASICs. |
| Parallelism | 4       | The number of independent computational threads. Utilizes modern multi-core processors. |
| Salt Length | 16      | The size of the random salt in bytes. Ensures unique hashes per user. |

These defaults align with OWASP and RFC 9106 recommendations for balanced secure password hashing.
