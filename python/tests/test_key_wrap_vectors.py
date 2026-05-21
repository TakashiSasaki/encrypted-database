import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
import pytest

from encrypted_storage import aad_policy

VECTOR_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../test-vectors/key-wrap/key-wrap-v1.json"
)

def load_vectors():
    with open(VECTOR_PATH, "r") as f:
        return json.load(f)

@pytest.mark.parametrize("vector", load_vectors())
def test_key_wrap_vector(vector):
    wrapping_key = bytes.fromhex(vector["wrapping_key_hex"])
    wrapped_key_plaintext = bytes.fromhex(vector["wrapped_key_plaintext_hex"])
    nonce = bytes.fromhex(vector["nonce_hex"])
    expected_aad = bytes.fromhex(vector["expected_aad_hex"])

    expected_ciphertext_and_tag = bytes.fromhex(vector["expected_wrapped_key_ciphertext_and_tag_hex"])

    # Verify AAD construction
    actual_aad = aad_policy.build_aad_bytes(
        vector["aad_policy"],
        wrapped_kid=vector["wrapped_kid"],
        wrapping_kid=vector["wrapping_kid"]
    )
    assert actual_aad.hex() == expected_aad.hex(), f"AAD mismatch for {vector['name']}"

    aesgcm = AESGCM(wrapping_key)

    if vector["valid"]:
        actual_ciphertext_and_tag = aesgcm.encrypt(nonce, wrapped_key_plaintext, actual_aad)
        assert actual_ciphertext_and_tag.hex() == expected_ciphertext_and_tag.hex(), f"Encryption mismatch for {vector['name']}"

        decrypted = aesgcm.decrypt(nonce, expected_ciphertext_and_tag, actual_aad)
        assert decrypted == wrapped_key_plaintext, f"Decryption mismatch for {vector['name']}"
    else:
        with pytest.raises(InvalidTag):
            aesgcm.decrypt(nonce, expected_ciphertext_and_tag, actual_aad)
