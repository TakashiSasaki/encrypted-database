import json
import os
import binascii
from encrypted_storage import crypto, aad_policy
import pytest

def encrypt_aead_fixed_nonce(key: bytes, nonce: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    return aesgcm.encrypt(nonce, plaintext, associated_data)

def test_payload_vectors():
    vectors_path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'payload', 'payload-encryption-v1.json')
    with open(vectors_path, 'r') as f:
        vectors = json.load(f)

    for v in vectors:
        record_dek = binascii.unhexlify(v['record_dek_hex'])
        nonce = binascii.unhexlify(v['nonce_hex'])
        expected_aad = binascii.unhexlify(v['expected_aad_hex'])
        expected_ct_tag = binascii.unhexlify(v['expected_ciphertext_and_tag_hex'])
        expected_jcs = v['expected_payload_jcs'].encode('utf-8')

        # AAD Policy Check
        aad_bytes = aad_policy.build_aad_bytes(
            "record-payload-v1",
            object_uuid=v['object_uuid'],
            schema_uuid=v['schema_uuid'],
            content_type=v['content_type'],
            kid=v['kid'],
            alg=v['alg']
        )
        assert aad_bytes == expected_aad, f"Payload vector '{v['name']}' AAD generation failed"

        # JCS payload logic
        payload_jcs = crypto.canonicalize_json(v['payload_json'])
        assert payload_jcs == expected_jcs, f"Payload vector '{v['name']}' JCS failed"

        # Encryption Check
        ct_tag = encrypt_aead_fixed_nonce(record_dek, nonce, payload_jcs, aad_bytes)
        assert ct_tag == expected_ct_tag, f"Payload vector '{v['name']}' encryption failed"

        # Decryption Check
        pt = crypto.decrypt_aead(record_dek, nonce, ct_tag, aad_bytes)
        assert pt == expected_jcs, f"Payload vector '{v['name']}' decryption failed"

        # Order invariance check
        reordered_payload = {k: v['payload_json'][k] for k in reversed(list(v['payload_json'].keys()))}
        reordered_jcs = crypto.canonicalize_json(reordered_payload)
        assert reordered_jcs == expected_jcs, f"Payload vector '{v['name']}' order invariance failed"
