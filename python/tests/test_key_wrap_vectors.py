import json
import os
import binascii
from encrypted_storage import crypto, aad_policy
import pytest

def encrypt_aead_fixed_nonce(key: bytes, nonce: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    return aesgcm.encrypt(nonce, plaintext, associated_data)

def test_key_wrap_vectors():
    vectors_path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'key-wrap', 'key-wrap-v1.json')
    with open(vectors_path, 'r') as f:
        vectors = json.load(f)

    for v in vectors:
        wrapping_key = binascii.unhexlify(v['wrapping_key_hex'])
        nonce = binascii.unhexlify(v['nonce_hex'])
        wrapped_key_pt = binascii.unhexlify(v['wrapped_key_plaintext_hex'])
        expected_ct_tag = binascii.unhexlify(v['expected_wrapped_key_ciphertext_and_tag_hex'])
        expected_aad = binascii.unhexlify(v['expected_aad_hex'])

        # Generate AAD dynamically
        aad_bytes = aad_policy.build_aad_bytes(
            v['aad_policy'],
            wrapped_kid=v['wrapped_kid'],
            wrapping_kid=v['wrapping_kid']
        )
        assert aad_bytes == expected_aad, f"Key-wrap vector '{v['name']}' AAD generation failed"

        # Wrap (Encrypt)
        ct_tag = encrypt_aead_fixed_nonce(wrapping_key, nonce, wrapped_key_pt, aad_bytes)
        assert ct_tag == expected_ct_tag, f"Key-wrap vector '{v['name']}' encryption failed"

        # Unwrap (Decrypt)
        pt = crypto.decrypt_aead(wrapping_key, nonce, ct_tag, aad_bytes)
        assert pt == wrapped_key_pt, f"Key-wrap vector '{v['name']}' decryption failed"
