from encrypted_storage import InvalidPassphrase, StorageError

def test_invalid_passphrase_export():
    assert issubclass(InvalidPassphrase, TypeError)
    assert not issubclass(InvalidPassphrase, StorageError)
