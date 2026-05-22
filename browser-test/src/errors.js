class InvalidPassphrase extends TypeError {
    constructor(message = "Passphrase must be a string") {
        super(message);
        this.name = "InvalidPassphrase";
    }
}

class StorageError extends Error {
    constructor(message) {
        super(message);
        this.name = this.constructor.name;
        Error.captureStackTrace(this, this.constructor);
    }
}

class StorageClosed extends StorageError {}
class StorageLocked extends StorageError {}
class StorageNotInitialized extends StorageError {}
class StorageAlreadyInitialized extends StorageError {}
class InvalidStorageFormat extends StorageError {}
class UnlockFailed extends StorageError {}
class ObjectNotFound extends StorageError {}
class UnsupportedPlatform extends StorageError {}
class InvalidUuid extends StorageError {}
class InvalidContentType extends StorageError {}
class InvalidPayload extends StorageError {}
class IntegrityCheckFailed extends StorageError {}
class CryptoOperationFailed extends StorageError {}
class DatabaseBackendError extends StorageError {}
class AadPolicyError extends StorageError {}

module.exports = {
    StorageError,
    StorageClosed,
    StorageLocked,
    StorageNotInitialized,
    StorageAlreadyInitialized,
    InvalidStorageFormat,
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
    InvalidPassphrase
};
