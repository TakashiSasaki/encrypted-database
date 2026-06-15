import json
import pytest
import os
import tempfile
from encrypted_storage.storage import EncryptedStorage
from encrypted_storage import errors

def get_vectors():
    with open(os.path.join(os.path.dirname(__file__), '../../test-vectors/uuid/uuid-v1.json'), 'r') as f:
        data = json.load(f)
    return data['vectors']

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

@pytest.mark.parametrize("vector", get_vectors())
def test_uuid_vector(temp_db, vector):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("pass", "linux")
    storage.unlock_database("pass")

    uuid_val = vector['uuid']
    is_valid = vector['valid']

    if is_valid:
        # Should not raise
        storage.store_payload(uuid_val, "application/json", {})
    else:
        with pytest.raises(errors.InvalidUuid):
            storage.store_payload(uuid_val, "application/json", {})

    storage.close()
