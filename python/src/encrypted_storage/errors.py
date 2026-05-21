class StorageError(Exception):
    """Base exception for all storage errors."""
    pass

class StorageClosed(StorageError):
    pass

class StorageLocked(StorageError):
    pass

class StorageNotInitialized(StorageError):
    pass

class StorageAlreadyInitialized(StorageError):
    pass

class UnlockFailed(StorageError):
    pass

class ObjectNotFound(StorageError):
    pass

class UnsupportedPlatform(StorageError):
    pass

class InvalidUuid(StorageError):
    pass

class InvalidContentType(StorageError):
    pass

class InvalidPayload(StorageError):
    pass

class IntegrityCheckFailed(StorageError):
    pass

class CryptoOperationFailed(StorageError):
    pass

class DatabaseBackendError(StorageError):
    pass

class AadPolicyError(StorageError):
    pass
