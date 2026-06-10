# C/C++ Native Conformance Roadmap

This document outlines the planned stages for expanding the C and C++ native conformance scaffolds. Currently, these implementations are strictly **bootstrap scaffolds** and are not production storage libraries.

They do not yet implement full Storage Format V1 cryptography, Argon2id, generic JSON Canonicalization Scheme (JCS), SQLite V1 read-only validation, writing capabilities, or integration into the read-only or write matrices.

The immediate goal is to incrementally establish a native testing boundary and validate cross-language test vectors before attempting integration.

## Roadmap Stages

1. **Bootstrap build/test scaffold** — done
2. **AAD shared-vector conformance** — partial/done (AAD construction conformance and internal escaping implemented)
3. **UUID syntax validation scaffold** — done (Internal conformance helpers implemented)
4. **Content-type boundary decision** — done (Internal boundary validation scaffold implemented)
5. **KDF dependency decision for Argon2id** — future
6. **AEAD dependency decision for AES-256-GCM** — future
7. **Key-wrap vector conformance** — future
8. **Payload encryption vector conformance** — future
9. **SQLite read-only fixture validation** — future
10. **Writer scaffold** — future
11. **Matrix integration** — future

*Note: This roadmap is intended for planning purposes only and does not imply that cryptographic or SQLite implementation work has commenced.*
