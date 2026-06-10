# C/C++ Content-Type Boundary Decision

## Overview

As part of the native conformance roadmap for C and C++, we have established an internal boundary-validation scaffold for the `content_type` property.

The C and C++ implementations provide an internal helper to validate the syntax of content types. This helper is **strictly internal** and is not exposed as a production public API.

## Design Decisions and Scope

*   **Not a Full MIME Parser:** The internal helper is not a full MIME token parser, nor does it validate the semantic correctness against an IANA MIME registry.
*   **Provisional Scaffold:** It serves as a provisional internal boundary to defend against malformed inputs and control characters within the C/C++ scaffold testing environment.
*   **No Normalization:** The helper does not lowercase, normalize, or canonicalize the input string. It preserves the exact case provided (e.g., `Application/JSON`).
*   **Whitespace:** The helper does not trim whitespace. Leading, trailing, or embedded spaces are accepted provided they meet the basic structural rules (i.e. they are not control characters).

## Validation Rules

The internal helper implements the following minimal conservative rule:

1.  **Non-Empty:** The input string must not be empty or `NULL`.
2.  **Basic Shape:** The string must contain exactly one forward slash (`/`).
3.  **Type/Subtype:** The portion before the slash (the "type") and the portion after the slash (the "subtype" and any parameters) must both be non-empty.
4.  **No Control Characters:** The string must not contain ASCII control characters (`0x00` through `0x1F`) or the DEL character (`0x7F`).
5.  **Printable ASCII and Non-ASCII:** Ordinary printable ASCII characters and non-ASCII bytes (e.g. UTF-8) are permitted as ordinary non-control bytes.

*(Note: While the Python and Node.js implementations currently perform a looser check that simply asserts `'/' in value`, the C/C++ scaffold explicitly tightens this to require exactly one slash to establish a stricter structural baseline without implementing full parameter parsing.)*
