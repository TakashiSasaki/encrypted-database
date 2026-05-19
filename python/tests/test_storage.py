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

    storage.close()

    storage2 = EncryptedStorage(temp_db)
    storage2.unlock_database("my_secure_password")
    retrieved2 = storage2.retrieve_payload(object_uuid)
    assert retrieved2 == payload
    storage2.close()

def test_initialization_fails_on_unknown_platform(temp_db):
    storage = EncryptedStorage(temp_db)
    with pytest.raises(ValueError, match="Unsupported platform"):
        storage.initialize_database("pass", "unknown_os")
    with pytest.raises(ValueError, match="cross_platform is not allowed"):
        storage.initialize_database("pass", "cross_platform")
    storage.close()

def test_store_fails_when_locked(temp_db):
    storage = EncryptedStorage(temp_db)
    with pytest.raises(ValueError, match="Database is locked"):
        storage.store_payload("id", "type", {})

def test_retrieve_fails_when_locked(temp_db):
    storage = EncryptedStorage(temp_db)
    try:
        with pytest.raises(ValueError, match="Database is locked"):
            storage.retrieve_payload("id")
    finally:
        storage.close()
    try:
        with pytest.raises(ValueError, match="Database is locked"):
            storage.store_payload("id", "type", {})
    finally:
        storage.close()

def test_retrieve_fails_if_not_found(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    with pytest.raises(ValueError, match="Object not found"):
        storage.retrieve_payload("00000000-0000-0000-0000-000000000000")
    storage.close()

def test_retrieve_fails_if_wrap_not_found(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    oid = storage.store_payload("00000000-0000-4000-8000-000000000001", "application/json", {})
    storage.conn.execute("PRAGMA foreign_keys = OFF")
    storage.conn.execute("UPDATE wrapped_key_tbl SET wrapped_kid = '00000000-0000-4000-8000-000000000000'")
    storage.conn.commit()
    with pytest.raises(ValueError, match="Record DEK wrap info not found"):
        storage.retrieve_payload(oid)
    storage.close()

def test_unlock_ignores_unknown_aad_policy(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    storage.conn.execute("UPDATE wrapped_key_tbl SET aad_policy = 'unknown'")
    storage.conn.commit()
    with pytest.raises(ValueError, match="Failed to unlock database"):
        storage.unlock_database("pass")
    storage.close()

def test_unlock_ignores_no_provider(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    storage.conn.execute("DELETE FROM unlock_kek_tbl")
    storage.conn.commit()
    with pytest.raises(ValueError, match="Failed to unlock database"):
        storage.unlock_database("pass")
    storage.close()

def test_unlock_fails_if_no_db_kek(temp_db):
    storage = EncryptedStorage(temp_db)
    try:
        with pytest.raises(ValueError, match="No active database KEK found"):
            storage.unlock_database("pass")
    finally:
        storage.close()

def test_initialize_database_rollback(temp_db):
    storage = EncryptedStorage(temp_db)

    # Drop table to force insert error
    storage.conn.execute("DROP TABLE wrapped_key_tbl")

    with pytest.raises(Exception):
        storage.initialize_database("pass", "linux")

    storage.close()

def test_store_payload_rollback(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")

    # Drop table to force insert error
    storage.conn.execute("DROP TABLE encrypted_object_tbl")

    with pytest.raises(Exception):
        storage.store_payload("00000000-0000-4000-8000-000000000001", "application/json", {})

    storage.close()

def test_close(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    storage.close()
    assert storage.active_db_kek is None
    assert storage.active_db_kid is None
