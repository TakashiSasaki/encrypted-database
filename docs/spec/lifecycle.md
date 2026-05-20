# Lifecycle States Diagram

This document illustrates the state transitions and lifecycle of the Encrypted Database, as defined in the [API Contract](api-contract.md).

## State Diagram

The following state diagram maps out the core lifecycle states (`uninitialized`, `open_locked`, `open_unlocked`, `closed`) and the API operations that drive the transitions between them. It also includes failure scenarios, such as when unlocking fails.

```mermaid
stateDiagram-v2
    [*] --> uninitialized

    uninitialized --> open_unlocked: initialize_database(passphrase, platform)\n[Success]
    uninitialized --> open_locked: (Implicit / Backend Initialized)\nIf database exists but is locked

    open_locked --> open_unlocked: unlock_database(passphrase)\n[Success]
    open_locked --> open_locked: unlock_database(passphrase)\n[Failure: UnlockFailed]

    open_unlocked --> open_locked: lock()\n[Explicit Lock]
    open_unlocked --> closed: close()\n[Explicit Close]

    open_locked --> closed: close()\n[Explicit Close]
    uninitialized --> closed: close()\n[Explicit Close]

    closed --> [*]

    note right of uninitialized
        Backend is not fully configured or ready.
    end note

    note right of open_locked
        Database is opened, but no active
        key material is in memory.
        Reads/Writes not permitted.
    end note

    note right of open_unlocked
        Active key material is loaded.
        Ready for read/write operations
        (e.g., store_payload, retrieve_payload).
    end note

    note right of closed
        Backend connection is closed.
        Key material is cleared.
        Terminal state.
    end note
```
