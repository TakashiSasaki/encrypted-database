import pytest
import tempfile
import os
from cryptography.exceptions import InvalidTag
from encrypted_storage.storage import EncryptedStorage
from encrypted_storage import errors

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
    with pytest.raises(errors.UnlockFailed):
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
    with pytest.raises(errors.UnsupportedPlatform):
        storage.initialize_database("pass", "cross_platform")
    storage.close()

def test_store_fails_when_locked(temp_db):
    storage = EncryptedStorage(temp_db)
    with pytest.raises(errors.StorageLocked):
        storage.store_payload("11111111-1111-4111-8111-111111111111", "application/json", {})

def test_retrieve_fails_when_locked(temp_db):
    storage = EncryptedStorage(temp_db)
    with pytest.raises(errors.StorageLocked):
        storage.retrieve_payload("11111111-1111-4111-8111-111111111111")
    with pytest.raises(errors.StorageLocked):
        storage.store_payload("11111111-1111-4111-8111-111111111111", "application/json", {})
    storage.close()

def test_retrieve_fails_if_not_found(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    with pytest.raises(errors.ObjectNotFound):
        storage.retrieve_payload("00000000-0000-4000-8000-000000000000")
    storage.close()

def test_retrieve_fails_if_wrap_not_found(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    oid = storage.store_payload("00000000-0000-4000-8000-000000000001", "application/json", {})
    storage.conn.execute("PRAGMA foreign_keys = OFF")
    storage.conn.execute("UPDATE wrapped_key_tbl SET wrapped_kid = '00000000-0000-4000-8000-000000000000'")
    storage.conn.commit()
    with pytest.raises(errors.IntegrityCheckFailed):
        storage.retrieve_payload(oid)
    storage.close()

def test_unlock_ignores_unknown_aad_policy(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    storage.conn.execute("UPDATE wrapped_key_tbl SET aad_policy = 'unknown'")
    storage.conn.commit()
    with pytest.raises(errors.UnlockFailed):
        storage.unlock_database("pass")
    storage.close()

def test_unlock_ignores_no_provider(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    storage.conn.execute("DELETE FROM unlock_kek_tbl")
    storage.conn.commit()
    with pytest.raises(errors.UnlockFailed):
        storage.unlock_database("pass")
    storage.close()

def test_unlock_fails_if_no_db_kek(temp_db):
    storage = EncryptedStorage(temp_db)
    try:
        with pytest.raises(errors.InvalidStorageFormat):
            storage.unlock_database("pass")
    finally:
        storage.close()

def test_initialize_database_rollback(temp_db):
    storage = EncryptedStorage(temp_db)
    storage._bootstrap_schema()

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

def test_aad_mutation_causes_decryption_failure(temp_db):
    """Test that altering an AAD-bound field in the database prevents decryption."""
    storage = EncryptedStorage(temp_db)
    storage.initialize_database(passphrase="secure-password", platform="linux")
    storage.unlock_database(passphrase="secure-password")

    object_uuid = storage.store_payload(
        schema_uuid="11111111-1111-4111-8111-111111111111",
        content_type="application/json",
        payload={"secret":"data"}
    )

    # Decrypt normally to confirm it works
    decrypted = storage.retrieve_payload(object_uuid)
    assert decrypted == {"secret":"data"}

    # Mutate the content_type in the database (which is bound to AAD)
    storage.conn.execute("UPDATE encrypted_object_tbl SET content_type = 'text/plain' WHERE object_uuid = ?", (object_uuid,))
    storage.conn.commit()

    # Attempt to retrieve, which should fail during AEAD decryption due to tag mismatch
    with pytest.raises(InvalidTag):
        storage.retrieve_payload(object_uuid)
