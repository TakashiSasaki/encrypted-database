# C/C++ Parser-Free JCS Model Conformance Review

## Status
Completed

## Purpose
This document summarizes the current C and C++ parser-free internal model conformance state. It explicitly compares the implemented behaviors against the accepted internal value model boundary, highlighting areas of parity, intentional limitations, and deferred work.

## Conformance Matrix

| Feature / Policy | C Implementation | C++ Implementation | Notes |
| :--- | :--- | :--- | :--- |
| **Supported Types** | `null`, `boolean`, `integer`, `string`, `array`, `object` | `null`, `boolean`, `integer`, `string`, `array`, `object` | Fully implemented in parser-free models. |
| **Safe Integer Range** | `[-9007199254740991, 9007199254740991]` | `[-9007199254740991, 9007199254740991]` | Hardened and checked on construction. |
| **Floating Point** | Unsupported (fails closed) | Unsupported (fails closed) | Not accepted by internal model functions. |
| **Exponent Notation** | Unsupported (fails closed) | Unsupported (fails closed) | Not accepted by internal model functions. |
| **Arbitrary Precision** | Unsupported (fails closed) | Unsupported (fails closed) | Fails safe-integer bounds checks. |
| **String Representation** | UTF-8 C string (`const char*`) | UTF-8 `std::string` | |
| **Embedded NUL (`\u0000`)** | Unsupported (inherent to C strings) | Unsupported (fails closed) | C++ explicitly rejects embedded NULs using length-aware checks. C uses null-terminated strings, inherently preventing embedded NULs. |
| **Invalid UTF-8 (Keys)** | Rejected (`VAULT_JCS_MODEL_ERROR_INVALID_ARG`) | Rejected (`ModelError::INVALID_ARG`) | Pre-validated before UTF-16 sorting. |
| **Invalid UTF-8 (Values)**| No explicit check yet | No explicit check yet | Current focus is on key ordering safety. Values are serialized as-is. |
| **Array Representation** | Deep-copied struct array | `std::shared_ptr` to vector | C++ uses shallow copy semantics for lifetimes. C uses deep copies. |
| **Object Representation**| Deep-copied struct array | `std::shared_ptr` to vector | C++ uses shallow copy semantics. |
| **Duplicate Key Policy** | Rejected (`VAULT_JCS_MODEL_ERROR_DUPLICATE_KEY`) | Rejected (`ModelError::DUPLICATE_KEY`) | Internal models actively reject duplicates during construction. |
| **Object Key Ordering** | UTF-16 code-unit ordering | UTF-16 code-unit ordering | Both implementations properly decode UTF-8 to UTF-16 code units for sorting, avoiding simple byte or locale ordering. No Unicode normalization is performed. |
| **Serializer Output** | Compact JSON | Compact JSON | No spaces outside strings. |
| **Control Escapes** | Lowercase `\u00xx` | Lowercase `\u00xx` | Both implementations conform to RFC 8785. |
| **Slash Escaping** | Not escaped | Not escaped | Both implementations conform to RFC 8785. |
| **UTF-8 Preservation** | Preserved | Preserved | Non-control UTF-8 is emitted unescaped. |
| **Error Mapping** | Maps to `VaultJcsModelError` enum | Maps to `ModelError` enum | Enums cover invalid arg, memory, unsafe int, duplicate key, etc. |

## Ownership and Copy Semantics
- **C Implementation:** Utilizes explicit deep copies for arrays and objects in its `init` functions. Memory allocation errors map to `VAULT_JCS_MODEL_ERROR_MEMORY` and ensure cleanup.
- **C++ Implementation:** Utilizes `std::shared_ptr` for composite types (Arrays/Objects) to provide shallow copy semantics. This prevents expensive deep copying while maintaining safe RAII lifetime management.

## Public / Internal Boundary Definition
- **Not a production public API:** The internal models are strictly for JCS generic testing and conformance. They are not intended for general public consumption yet.
- **Not a raw JSON parser:** These models require explicit programmatic construction. The complex work of parsing arbitrary raw JSON text is explicitly deferred.
- **Not SQLite / Provider Config Validation:** This layer exists strictly to serialize internal values to JSON strings.

## Open Gaps and Intentionally Deferred Work
- **Raw JSON Parsing:** Explicitly deferred.
- **Generic JSON Vector Loader:** Explicitly deferred to the next architectural stride.
- **Rejection-Vector Harness:** Explicitly deferred until the raw JSON parser and generic vector loader exist.
- **Active UTF-16 Verification Hooks:** While UTF-16 ordering is implemented internally, it is not yet hooked up to active C/C++ cross-language bridge tests. The standalone `utf16-key-ordering.json` file remains a separate seed pending the generic vector loader.
- **Value UTF-8 Validation:** Strings values are currently serialized as-is; invalid UTF-8 is only strictly caught for object keys to prevent undefined behavior during UTF-16 conversion.
