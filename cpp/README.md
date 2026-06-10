# C++ Bootstrap Scaffold

This directory contains the initial C++ bootstrap scaffold for the Encrypted Database project.

## Status

**This is strictly a bootstrap scaffold. It is not a production storage library.**
It does not currently implement any Storage Format V1 capabilities (e.g., cryptography, SQLite V1 reading/writing, Argon2id, JCS, AAD, or matrix integration). Public API parity is not yet promised.

**Architecture Status:** `needs-decision`
It is not yet decided whether this C++ implementation will eventually wrap a common C core layer or remain a completely separate C++ implementation.

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
cd cpp
cmake -S . -B build
cmake --build build
ctest --test-dir build --output-on-failure
```
