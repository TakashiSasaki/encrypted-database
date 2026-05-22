from encrypted_storage import (
    StorageError,
    StorageClosed,
    StorageLocked,
    StorageNotInitialized,
    StorageAlreadyInitialized,
    UnlockFailed,
    ObjectNotFound,
    UnsupportedPlatform,
    InvalidUuid,
    InvalidContentType,
    InvalidPayload,
    IntegrityCheckFailed,
    CryptoOperationFailed,
    DatabaseBackendError,
    AadPolicyError,
    InvalidPassphrase,
)

import encrypted_storage

def test_top_level_error_exports():
    # Test that __all__ contains the expected error classes
    expected_exports = {
        "StorageError",
        "StorageClosed",
        "StorageLocked",
        "StorageNotInitialized",
        "StorageAlreadyInitialized",
        "UnlockFailed",
        "ObjectNotFound",
        "UnsupportedPlatform",
        "InvalidUuid",
        "InvalidContentType",
        "InvalidPayload",
        "IntegrityCheckFailed",
        "CryptoOperationFailed",
        "DatabaseBackendError",
        "AadPolicyError",
        "InvalidPassphrase",
    }

    for expected_export in expected_exports:
        assert expected_export in encrypted_storage.__all__

    # Test InvalidPassphrase inheritance
    assert issubclass(InvalidPassphrase, TypeError)
    assert not issubclass(InvalidPassphrase, StorageError)

    # Test InvalidPayload inheritance
    assert issubclass(InvalidPayload, StorageError)

    # Test other StorageError subclasses to ensure everything exported properly
    assert issubclass(StorageClosed, StorageError)
    assert issubclass(StorageLocked, StorageError)
    assert issubclass(StorageNotInitialized, StorageError)
    assert issubclass(StorageAlreadyInitialized, StorageError)
    assert issubclass(UnlockFailed, StorageError)
    assert issubclass(ObjectNotFound, StorageError)
    assert issubclass(UnsupportedPlatform, StorageError)
    assert issubclass(InvalidUuid, StorageError)
    assert issubclass(InvalidContentType, StorageError)
    assert issubclass(IntegrityCheckFailed, StorageError)
    assert issubclass(CryptoOperationFailed, StorageError)
    assert issubclass(DatabaseBackendError, StorageError)
    assert issubclass(AadPolicyError, StorageError)
