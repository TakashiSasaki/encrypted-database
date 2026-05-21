import pytest
from encrypted_storage.storage import EncryptedStorage
from encrypted_storage import errors
import tempfile
import os

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

def test_validate_uuid(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")

    # Missing hyphens
    with pytest.raises(errors.InvalidUuid):
        storage.store_payload("a2345678123442348234123456789012", "application/json", {})

    # Uppercase
    with pytest.raises(errors.InvalidUuid):
        storage.store_payload("A2345678-1234-4234-8234-123456789012", "application/json", {})

    # Not string
    with pytest.raises(errors.InvalidUuid):
        storage.store_payload(None, "application/json", {})

def test_validate_content_type(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    schema_uuid = "12345678-1234-4234-8234-123456789012"

    with pytest.raises(errors.InvalidContentType):
        storage.store_payload(schema_uuid, "", {})

    with pytest.raises(errors.InvalidContentType):
        storage.store_payload(schema_uuid, "applicationjson", {})  # no slash

    with pytest.raises(errors.InvalidContentType):
        storage.store_payload(schema_uuid, "application/json\x00", {})

def test_validate_payload(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    schema_uuid = "12345678-1234-4234-8234-123456789012"

    with pytest.raises(errors.InvalidPayload):
        storage.store_payload(schema_uuid, "application/json", [])

    with pytest.raises(errors.InvalidPayload):
        storage.store_payload(schema_uuid, "application/json", "string")

    with pytest.raises(errors.InvalidPayload):
        storage.store_payload(schema_uuid, "application/json", None)

def test_validate_passphrase(temp_db):
    storage = EncryptedStorage(temp_db)
    with pytest.raises(errors.UnlockFailed):
        storage.initialize_database(None, "linux")

    # Empty string is allowed
    storage.initialize_database("", "linux")

def test_retrieve_uuid_validation(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")

    with pytest.raises(errors.InvalidUuid):
        storage.retrieve_payload("invalid-uuid")
