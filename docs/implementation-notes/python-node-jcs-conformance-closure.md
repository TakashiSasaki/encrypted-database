# Python/Node.js JCS Conformance Closure

## Purpose
This document finalizes the JSON Canonicalization Scheme (JCS) conformance status for the Python and Node.js storage libraries. It explicitly classifies all existing JCS vector files and documents exactly which vectors are consumed by the implementations, allowing for the removal of vague blockers regarding unclassified JCS conformance coverage gaps.

## JCS Vector Classification
The `test-vectors/jcs/` directory contains the following files:

| File | Classification | Consumed by Python/Node.js? | Notes |
|---|---|---|---|
| `rfc8785-basic.json` | active executable positive vector | Yes | Basic JSON canonicalization aspects safe for all current implementations. |
| `generic-positive-coverage.json` | active executable positive vector | Yes | Strictly safe positive vectors (no floats, no unsafe integers, no duplicates, no embedded NUL). |
| `utf16-key-ordering.json` | C/C++ scaffold-only vector (non-active positive seed) | No | Non-ASCII keys and surrogate-pair sensitive ordering as per RFC 8785. Cannot be safely wired into Python (`jcs` package) and Node.js (`json-canonicalize` package) without custom raw parsers, as standard parsers often silently re-order or mishandle duplicates/surrogates before the canonicalization library receives the AST. |
| `future-boundary-plan.json` | future/planning-only vector | No | Planning only. Contains expected errors/rejections (e.g., duplicate keys, embedded NULs, unsafe integers). Unsupported by current generic-AST serializers. |

## Conformance Closure Outcome
Python and Node.js explicitly consume all safe, active, executable positive JCS vectors (`rfc8785-basic.json`, `generic-positive-coverage.json`).

There are **no active executable negative/rejection JCS vectors** currently designed for test-runner consumption. By design, `future-boundary-plan.json` is for planning only, and `utf16-key-ordering.json` is deferred from CI consumption because standard Python and Node.js parsers (which back the JCS canonicalization packages) cannot natively execute raw parser-boundary testing without a future generic JSON parser implementation.

Adding future vectors or rejection vectors at this stage would require unsupported raw parser implementations or change Storage Format V1 semantics, which is explicitly out of scope for the current `baseline-public` stride.

As a result, no vague unclassified JCS conformance coverage blockers remain for Python and Node.js.

**Status: Ready for reviewer sign-off.**
