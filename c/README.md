# C Bootstrap Scaffold

This directory contains the initial C bootstrap scaffold for the Encrypted Database project.

## Status

**This is strictly a bootstrap scaffold. It is not a production storage library.**
It does not currently implement Storage Format V1 cryptography, SQLite V1 reading/writing, Argon2id, generic JCS, or matrix integration. It provides partial AAD shared-vector conformance through internal scaffold helpers. Public API parity is not yet promised.

## Future Milestones
1. UUID/content-type/JCS boundary decisions
2. Argon2id/AES-256-GCM dependency selection
3. SQLite V1 read-only validation
4. selected fixture decrypt
5. writer scaffold
6. read-only/write matrix integration

*Completed:*
- shared-vector parsing and deterministic test harness (partial: AAD construction conformance)

## Testing

You can run the smoke tests locally using CMake:

```bash
cd c
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```
