import json
import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
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

    # Verify AAD reconstruction
    actual_aad = aad_policy.build_aad_bytes(
        "record-payload-v1",
        object_uuid=vector["object_uuid"],
        schema_uuid=vector["schema_uuid"],
        content_type=vector["content_type"],
        kid=vector["kid"],
        alg=vector["alg"]
    )

    aesgcm = AESGCM(record_dek)

    if vector["valid"]:
        assert actual_aad.hex() == expected_aad.hex(), f"AAD mismatch for {vector['name']}"
        actual_ciphertext_and_tag = aesgcm.encrypt(nonce, actual_payload_jcs, actual_aad)
        assert actual_ciphertext_and_tag.hex() == expected_ciphertext_and_tag.hex(), f"Encryption mismatch for {vector['name']}"

        decrypted = aesgcm.decrypt(nonce, expected_ciphertext_and_tag, actual_aad)
        assert decrypted == actual_payload_jcs, f"Decryption mismatch for {vector['name']}"
    else:
        # In negative tests like invalid AAD, the generated expected_aad in the JSON
        # might be the "wrong" AAD itself, which means actual_aad might match the wrong one
        # (since we are testing decryption with actual_aad).
        # We ensure it fails with actual_aad against the original ciphertext.
        with pytest.raises(InvalidTag):
            aesgcm.decrypt(nonce, expected_ciphertext_and_tag, actual_aad)
