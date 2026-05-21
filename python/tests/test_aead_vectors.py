import json
import os
import binascii
from encrypted_storage import crypto
import pytest
from cryptography.exceptions import InvalidTag

def encrypt_aead_fixed_nonce(key: bytes, nonce: bytes, plaintext: bytes, associated_data: bytes) -> bytes:
    # Use internal implementation to test fixed nonce
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aesgcm = AESGCM(key)
    return aesgcm.encrypt(nonce, plaintext, associated_data)

def decrypt_aead_fixed_nonce(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes) -> bytes:
    return crypto.decrypt_aead(key, nonce, ciphertext, associated_data)


def test_aead_vectors():
    vectors_path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'aead', 'aes-256-gcm-v1.json')
    with open(vectors_path, 'r') as f:
        vectors = json.load(f)

    for v in vectors:
        key = binascii.unhexlify(v['key_hex'])
        nonce = binascii.unhexlify(v['nonce_hex'])
        aad = binascii.unhexlify(v['aad_hex'])
        plaintext = binascii.unhexlify(v['plaintext_hex'])
        expected_ct_tag = binascii.unhexlify(v['expected_ciphertext_and_tag_hex'])

        # Encrypt
        ct_tag = encrypt_aead_fixed_nonce(key, nonce, plaintext, aad)
        assert ct_tag == expected_ct_tag, f"AEAD vector '{v['name']}' encryption failed"

        # Decrypt
        pt = decrypt_aead_fixed_nonce(key, nonce, ct_tag, aad)
        assert pt == plaintext, f"AEAD vector '{v['name']}' decryption failed"

        # Negative tests
        # Corrupt tag (last byte)
        corrupted_ct_tag = ct_tag[:-1] + bytes([ct_tag[-1] ^ 0xFF])
        with pytest.raises(InvalidTag):
            decrypt_aead_fixed_nonce(key, nonce, corrupted_ct_tag, aad)

        # Corrupt AAD
        corrupted_aad = aad + b"a"
        with pytest.raises(InvalidTag):
            decrypt_aead_fixed_nonce(key, nonce, ct_tag, corrupted_aad)
