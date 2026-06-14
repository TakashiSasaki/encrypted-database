# Baseline-Public Readiness Gap Analysis

## Purpose
This document defines the remaining gaps before the `Python` and `Node.js` test-wrapper baseline candidates can be safely promoted to `baseline-public`. Test-wrapper compatibility success is explicitly **not release certification**.

This analysis builds upon the findings in the [Python and Node.js Baseline-Public API and Error Semantics Audit](python-node-baseline-public-api-error-semantics-audit.md).

## Readiness Table

| Dimension | Python | Node.js | Description |
|---|---|---|---|
| Public read API surface | implemented-public* | implemented-public* | API surface exists and is aligned; final semantic review pending |
| Public write API surface | implemented-public* | implemented-public* | API surface exists and is aligned; final semantic review pending |
| Storage Format V1 semantic stability | pending | pending | Verify no hidden assumptions before locking public API |
| Shared conformance vectors | expanded-positive-vectors-wired | expanded-positive-vectors-wired | Core positive vector suites are wired, but full RFC 8785 vector coverage verification required across libraries |
| Cross-language wrapper evidence | test-wrapper-passed | test-wrapper-passed | Successfully executes via temporary testing wrappers |
| CI evidence | path-filtered | path-filtered | Ensure robust pipeline execution |
| Package metadata | partial | partial | Needs comprehensive documentation and correct publish metadata |
| Public docs | partial | partial | End-user API docs required before baseline-public promotion |
| API/error semantics | implemented-public* | implemented-public* | Vocabulary aligned; pending final cross-language error code mapping consistency review |
| Security notes | pending | pending | Review payload boundaries, key management, and JCS constraints |
| Release-readiness review | pending | pending | Final architectural and security sign-off |

\* `implemented-public` indicates that the code exists, but it has not been certified as stable or baseline-public.

## Promotion Checklist
Before declaring any language `baseline-public`, the following must be completed:
- [ ] Stabilize the public API interface.
- [ ] Integrate full shared conformance vectors (JCS, AAD, AES-GCM, UUID).
- [ ] Formalize API/error semantics across languages.
- [ ] Publish clear end-user documentation.
- [ ] Prepare comprehensive package metadata.
- [ ] Complete security and release-readiness review.
- [ ] Demonstrate cross-language compatibility through stable public APIs (not just test wrappers).

## Non-Goals
This stride does not promote any language to `baseline-public`. It solely establishes the gap analysis and tracking mechanism for future completion.
