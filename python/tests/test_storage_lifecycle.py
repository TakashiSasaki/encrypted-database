import pytest
from encrypted_storage.storage import EncryptedStorage
from encrypted_storage import errors

def test_lifecycle(tmp_path):
    db_path = tmp_path / "test.db"

    # 1. Uninitialized
    storage = EncryptedStorage(str(db_path))
    assert storage.get_status() == "uninitialized"
    assert not storage.is_unlocked()
    assert not storage.is_closed()

    # 2. Lock should not crash but should just clear nothing since there's no db
    storage.lock()

    # 3. Store should fail
    with pytest.raises(errors.StorageLocked):
        storage.store_payload("schema", "type", {})

    # 4. Initialize
    storage.initialize_database("pass", "linux")
    assert storage.get_status() == "open_unlocked"
    assert storage.is_unlocked()

    # 5. Lock
    storage.lock()
    assert storage.get_status() == "open_locked"
    assert not storage.is_unlocked()

    # 6. Unlock
    storage.unlock_database("pass")
    assert storage.get_status() == "open_unlocked"

    # 7. Close
    storage.close()
    assert storage.get_status() == "closed"
    assert storage.is_closed()
    assert not storage.is_unlocked()

    # 8. Close is idempotent
    storage.close()

    # 9. Operations fail on close
    with pytest.raises(errors.StorageClosed):
        storage.lock()

    with pytest.raises(errors.StorageClosed):
        storage.initialize_database("pass", "linux")

    with pytest.raises(errors.StorageClosed):
        storage.unlock_database("pass")

    with pytest.raises(errors.StorageClosed):
        storage.store_payload("schema", "type", {})

    with pytest.raises(errors.StorageClosed):
        storage.retrieve_payload("some-uuid")

def test_unlock_failure_clears_keys(tmp_path):
    db_path = tmp_path / "test2.db"
    storage = EncryptedStorage(str(db_path))
    storage.initialize_database("correct_pass", "linux")
    assert storage.is_unlocked()

    with pytest.raises(errors.UnlockFailed):
        storage.unlock_database("wrong_pass")

    assert not storage.is_unlocked()
    assert storage.get_status() == "open_locked"

def test_duplicate_initialize(tmp_path):
    db_path = tmp_path / "test3.db"
    storage = EncryptedStorage(str(db_path))
    storage.initialize_database("pass", "linux")

    with pytest.raises(errors.StorageAlreadyInitialized):
        storage.initialize_database("pass", "linux")

    storage.lock()
    with pytest.raises(errors.StorageAlreadyInitialized):
        storage.initialize_database("pass", "linux")
