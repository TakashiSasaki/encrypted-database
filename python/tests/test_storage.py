import pytest
import tempfile
import os
from encrypted_storage.storage import EncryptedStorage

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

def test_initialization_and_unlock(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("my_secure_password", "linux")
    storage.close()

    storage2 = EncryptedStorage(temp_db)
    with pytest.raises(ValueError):
        storage2.unlock_database("wrong_password")

    storage2.unlock_database("my_secure_password")
    assert storage2.active_db_kek is not None
    storage2.close()

def test_store_and_retrieve_payload(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("my_secure_password", "linux")

    payload = {"secret": "data", "value": 42}
    schema_uuid = "00000000-0000-4000-8000-000000000001"

    object_uuid = storage.store_payload(schema_uuid, "application/json", payload)

    retrieved = storage.retrieve_payload(object_uuid)
    assert retrieved == payload

    # Test retrieving with a new instance
    storage.close()

    storage2 = EncryptedStorage(temp_db)
    storage2.unlock_database("my_secure_password")
    retrieved2 = storage2.retrieve_payload(object_uuid)
    assert retrieved2 == payload
    storage2.close()
