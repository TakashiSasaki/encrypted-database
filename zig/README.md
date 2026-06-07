# Zig Component

This is currently only a Zig smoke-test component to prove that Zig source files, build configuration, executable build, and tests can work in this repository.

The Zig smoke test is intended to run on the stable Zig version pinned by `.github/workflows/test-zig.yml`.

**It is not yet a Storage Format V1 implementation.**

## Commands

Run the executable:
```bash
zig build run
```

Run unit tests:
```bash
zig build test
```
