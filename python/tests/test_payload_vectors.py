import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import pytest
import jcs

from encrypted_storage import aad_policy

VECTOR_PATH = os.path.join(
    os.path.dirname(__file__),
    "../../test-vectors/payload/payload-encryption-v1.json"
)

def load_vectors():
    with open(VECTOR_PATH, "r") as f:
        return json.load(f)

@pytest.mark.parametrize("vector", load_vectors())
def test_payload_vector(vector):
    record_dek = bytes.fromhex(vector["record_dek_hex"])
    nonce = bytes.fromhex(vector["nonce_hex"])
    expected_aad = bytes.fromhex(vector["expected_aad_hex"])
    expected_payload_jcs = bytes.fromhex(vector["expected_payload_jcs_hex"])
    expected_ciphertext_and_tag = bytes.fromhex(vector["expected_ciphertext_and_tag_hex"])

    # Verify JCS
    actual_payload_jcs = jcs.canonicalize(vector["payload_json"])
    assert actual_payload_jcs.hex() == expected_payload_jcs.hex(), f"JCS mismatch for {vector['name']}"

    # For AAD generation, only use valid vector data if it's the valid flow,
    # otherwise we use what's generated. But in test, we just compare to expected.

    aesgcm = AESGCM(record_dek)

    if vector["valid"]:
        actual_ciphertext_and_tag = aesgcm.encrypt(nonce, actual_payload_jcs, expected_aad)
        assert actual_ciphertext_and_tag.hex() == expected_ciphertext_and_tag.hex(), f"Encryption mismatch for {vector['name']}"

        decrypted = aesgcm.decrypt(nonce, expected_ciphertext_and_tag, expected_aad)
        assert decrypted == actual_payload_jcs, f"Decryption mismatch for {vector['name']}"
    else:
        with pytest.raises(Exception):
            aesgcm.decrypt(nonce, expected_ciphertext_and_tag, expected_aad)
