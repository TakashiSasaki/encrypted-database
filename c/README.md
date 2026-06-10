# C Bootstrap Scaffold

This directory contains the initial C bootstrap scaffold for the Encrypted Database project.

## Status

**This is strictly a bootstrap scaffold. It is not a production storage library.**
It does not currently implement any Storage Format V1 capabilities (e.g., cryptography, SQLite V1 reading/writing, Argon2id, JCS, AAD, or matrix integration). Public API parity is not yet promised.

## Future Milestones
1. shared-vector parsing and deterministic test harness
2. UUID/content-type/JCS boundary decisions
3. AAD construction conformance
4. Argon2id/AES-256-GCM dependency selection
5. SQLite V1 read-only validation
6. selected fixture decrypt
7. writer scaffold
8. read-only/write matrix integration

## Testing

You can run the smoke tests locally using CMake:

```bash
cd c
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```
