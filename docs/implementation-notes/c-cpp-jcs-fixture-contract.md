# C/C++ JCS Generated-AST Fixture Contract

## Overview
To validate JCS functionality without requiring a third-party parser, the C and C++ bootstrap scaffolds rely on a test harness generator (`scripts/generate_jcs_test_vectors.py`). This generator consumes shared JSON vectors (`test-vectors/jcs/rfc8785-basic.json`) and emits an Abstract Syntax Tree (AST) representing the parsed JCS test vector elements in C-structs.

To mitigate duplication and reduce drift risk, C and C++ share a single generated-AST test-fixture layout contract defined in `c/src/vault_jcs_internal.h`.

## Key Principles

- **It is an internal test-harness contract.** The generated AST data structure is only for feeding test vectors into the native implementation serializers. It acts as a seed for future generic JCS conformance planning, not as a replacement for a generic parser or canonicalizer design.
- **It is not a runtime storage format.** The database and its API do not operate on this layout.
- **It is not a public API.** These structures exist purely in internal headers.
- **It does not override the independent implementation architecture.** C and C++ share the *layout definition* so the generator outputs one header, but the serialization implementation remains completely separate and idiomatic to each language. C++ must not wrap or call the C serializer implementation. Future generic JCS implementations must not silently inherit the simplified sorting and number limitations of this scaffold.

## Layout and Sorting Expectations

- The generator preserves the original source object order from the JSON vector.
- The *serializer* (not the generator) is responsible for sorting object keys lexicographically based on UTF-16 code units (or equivalent simple byte comparison when acceptable).
- This ensures that the scaffold sorting logic is genuinely exercised and verified against the expected canonical string.

## Supported and Unsupported Types

For a full classification of test vectors and policies on what is safely included, refer to the [JCS Vector Classification](./jcs-vector-classification.md) document.

### Supported by the Fixture Contract
The current generated-AST fixture contract supports only the following types:
- objects (with basic string keys, and ASCII-based ordering)
- arrays
- strings (with required JSON escaping, ASCII focus, and basic Unicode preservation)
- signed 64-bit integers
- booleans
- null

### Explicitly Unsupported
- **Floats / Decimals:** Storage Format V1 explicitly avoids float canonicalization where possible. The generator fails closed if floats are encountered.
- **Arbitrary precision numbers**
- **Arbitrary JSON parsing**
- **Public JCS API validation**
- **Provider config and database metadata validation**
- **Cryptographic use**
