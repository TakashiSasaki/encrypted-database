import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import pytest

VECTOR_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../test-vectors/aead/aes-256-gcm-v1.json"
)

def load_vectors():
    with open(VECTOR_PATH, "r") as f:
        return json.load(f)

@pytest.mark.parametrize("vector", load_vectors())
def test_aead_vector(vector):
    key = bytes.fromhex(vector["key_hex"])
    nonce = bytes.fromhex(vector["nonce_hex"])
    aad = bytes.fromhex(vector["aad_hex"])
    plaintext = bytes.fromhex(vector["plaintext_hex"])

    expected_ciphertext_and_tag = bytes.fromhex(vector["expected_ciphertext_and_tag_hex"])
    expected_ciphertext = bytes.fromhex(vector["expected_ciphertext_hex"])
    expected_tag = bytes.fromhex(vector["expected_tag_hex"])

    aesgcm = AESGCM(key)

    if vector["valid"]:
        # Test encryption
        actual_ciphertext_and_tag = aesgcm.encrypt(nonce, plaintext, aad)
        assert actual_ciphertext_and_tag.hex() == expected_ciphertext_and_tag.hex(), f"Encryption failed for {vector['name']}"

        actual_ciphertext = actual_ciphertext_and_tag[:-16]
        actual_tag = actual_ciphertext_and_tag[-16:]
        assert actual_ciphertext.hex() == expected_ciphertext.hex(), f"Ciphertext mismatch for {vector['name']}"
        assert actual_tag.hex() == expected_tag.hex(), f"Tag mismatch for {vector['name']}"

        # Test decryption
        decrypted = aesgcm.decrypt(nonce, expected_ciphertext_and_tag, aad)
        assert decrypted == plaintext, f"Decryption failed for {vector['name']}"
    else:
        # Negative tests
        with pytest.raises(InvalidTag):
            aesgcm.decrypt(nonce, expected_ciphertext_and_tag, aad)
