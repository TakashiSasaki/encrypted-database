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

    # Top level rejections
    with pytest.raises(errors.InvalidPayload):
        storage.store_payload(schema_uuid, "application/json", [])

    with pytest.raises(errors.InvalidPayload):
        storage.store_payload(schema_uuid, "application/json", "string")

    with pytest.raises(errors.InvalidPayload):
        storage.store_payload(schema_uuid, "application/json", None)

    # Valid deeply nested payload
    valid_payload = {
        "a": "string",
        "b": 123,
        "c": 45.67,
        "d": True,
        "e": False,
        "f": None,
        "g": [1, "two", {"three": 3}],
        "h": {"nested": {"deep": [True, False, None]}}
    }
    storage.store_payload(schema_uuid, "application/json", valid_payload)

    # Reject binary data
    with pytest.raises(errors.InvalidPayload, match="unsupported type bytes"):
        storage.store_payload(schema_uuid, "application/json", {"data": b"bytes"})
    with pytest.raises(errors.InvalidPayload, match="unsupported type bytearray"):
        storage.store_payload(schema_uuid, "application/json", {"data": bytearray(b"bytes")})
    with pytest.raises(errors.InvalidPayload, match="unsupported type memoryview"):
        storage.store_payload(schema_uuid, "application/json", {"data": memoryview(b"bytes")})

    # Reject non-string dictionary keys
    with pytest.raises(errors.InvalidPayload, match="dictionary keys must be strings"):
        storage.store_payload(schema_uuid, "application/json", {123: "value"})
    with pytest.raises(errors.InvalidPayload, match="dictionary keys must be strings"):
        storage.store_payload(schema_uuid, "application/json", {"nested": {True: "value"}})

    # Reject NaN and Infinity
    with pytest.raises(errors.InvalidPayload, match="NaN and Infinity are not valid JSON"):
        storage.store_payload(schema_uuid, "application/json", {"num": float("nan")})
    with pytest.raises(errors.InvalidPayload, match="NaN and Infinity are not valid JSON"):
        storage.store_payload(schema_uuid, "application/json", {"num": float("inf")})
    with pytest.raises(errors.InvalidPayload, match="NaN and Infinity are not valid JSON"):
        storage.store_payload(schema_uuid, "application/json", {"num": float("-inf")})

    # Reject sets and tuples
    with pytest.raises(errors.InvalidPayload, match="unsupported type set"):
        storage.store_payload(schema_uuid, "application/json", {"data": {1, 2, 3}})
    with pytest.raises(errors.InvalidPayload, match="unsupported type tuple"):
        storage.store_payload(schema_uuid, "application/json", {"data": (1, 2, 3)})

    # Reject arbitrary objects
    class Dummy:
        pass
    with pytest.raises(errors.InvalidPayload, match="unsupported type Dummy"):
        storage.store_payload(schema_uuid, "application/json", {"data": Dummy()})

    # Reject cyclic references
    cyclic_dict = {}
    cyclic_dict['self'] = cyclic_dict
    with pytest.raises(errors.InvalidPayload, match="cyclic reference"):
        storage.store_payload(schema_uuid, "application/json", cyclic_dict)

    cyclic_list = []
    cyclic_list.append(cyclic_list)
    with pytest.raises(errors.InvalidPayload, match="cyclic reference"):
        storage.store_payload(schema_uuid, "application/json", {"data": cyclic_list})


def test_validate_passphrase(temp_db):
    storage = EncryptedStorage(temp_db)
    with pytest.raises(TypeError):
        storage.initialize_database(None, "linux")

    # Empty string is allowed
    storage.initialize_database("", "linux")

    # unlock_database raises TypeError for invalid types
    storage.close()
    storage = EncryptedStorage(temp_db)
    with pytest.raises(TypeError):
        storage.unlock_database(None)


def test_retrieve_uuid_validation(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")

    with pytest.raises(errors.InvalidUuid):
        storage.retrieve_payload("invalid-uuid")

def test_closed_state_precedence(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    storage.close()

    # Closed check should happen before input validation
    with pytest.raises(errors.StorageClosed):
        storage.store_payload("invalid-uuid", "", [])

    with pytest.raises(errors.StorageClosed):
        storage.retrieve_payload("invalid-uuid")

    with pytest.raises(errors.StorageClosed):
        storage.initialize_database(123, 456)

    with pytest.raises(errors.StorageClosed):
        storage.unlock_database(123)
