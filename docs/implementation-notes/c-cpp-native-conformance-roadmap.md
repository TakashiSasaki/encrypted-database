# C/C++ Native Conformance Roadmap

This document outlines the planned stages for expanding the C and C++ native conformance scaffolds. Currently, these implementations are strictly **bootstrap scaffolds** and are not production storage libraries.

They do not yet implement full Storage Format V1 cryptography, Argon2id, generic JSON Canonicalization Scheme (JCS), SQLite V1 read-only validation, writing capabilities, or integration into the read-only or write matrices.

The immediate goal is to incrementally establish a native testing boundary and validate cross-language test vectors before attempting integration.

## Roadmap Stages

### Completed
- **Bootstrap build/test scaffold**
- **Partial AAD shared-vector conformance**
- **Internal JSON escaping for AAD construction**
- **Internal UUID syntax validation scaffold**
- **Internal content-type boundary validation scaffold**
- **Documentation consistency cleanup**
- **JCS scaffold boundary decision**
- **Limited generated-AST JCS basic-vector serializer scaffold**
- **C/C++ independent implementation architecture decision**
- **JCS fixture contract cleanup**

### Future
- **Generic JCS implementation**
- **Argon2id dependency decision**
- **Argon2id vector conformance**
- **AES-256-GCM dependency decision**
- **AEAD vector conformance**
- **Key-wrap vector conformance**
- **Payload encryption vector conformance**
- **SQLite read-only fixture validation**
- **Read-only decrypt scaffold**
- **Writer scaffold**
- **Matrix integration**
- **Production public API decision**

## Next: Generic JCS implementation

Before proceeding to implement generic JCS, the project must decide:
- dependency-free internal implementation vs third-party library
- JSON parser decision or implementation if appropriate
- RFC 8785 coverage boundary beyond basic vectors

*Note: This roadmap is intended for planning purposes only and does not imply that cryptographic or SQLite implementation work has commenced.*
