import pytest
import tempfile
import os
import json
from encrypted_storage.storage import EncryptedStorage
from encrypted_storage import crypto

@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp()
    os.close(fd)
    yield path
    os.unlink(path)

def test_initialization_saves_correct_profile(temp_db):
    storage = EncryptedStorage(temp_db)
    storage.initialize_database("my_secure_password", "linux")

    # Read provider config from DB
    cursor = storage.conn.execute("SELECT provider_config_json FROM unlock_kek_tbl LIMIT 1")
    row = cursor.fetchone()
    assert row is not None

    config_json = row[0]
    config = json.loads(config_json)

    # Check parameters
    assert config["memory_kib"] == 65536
    assert config["iterations"] == 3
    assert config["parallelism"] == 1
    assert "salt" in config

    storage.close()

def test_argon2id_test_vector():
    # Load test vector
    vector_path = os.path.join(os.path.dirname(__file__), "..", "..", "test-vectors", "kdf", "argon2id-v1.json")
    with open(vector_path, "r") as f:
        vectors = json.load(f)

    vector = vectors[0]

    passphrase = vector["input"]["passphrase"]
    salt = bytes.fromhex(vector["input"]["salt_hex"])

    expected_output = bytes.fromhex(vector["expected_output_hex"])

    # Derive
    derived = crypto.derive_kek_argon2id(
        password=passphrase,
        salt=salt,
        length=vector["parameters"]["output_bytes"],
        time_cost=vector["parameters"]["iterations"],
        memory_cost=vector["parameters"]["memory_kib"],
        parallelism=vector["parameters"]["parallelism"]
    )

    assert derived == expected_output
