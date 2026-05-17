import os
import json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

def generate_random_bytes(length: int = 32) -> bytes:
    return os.urandom(length)

def generate_nonce() -> bytes:
    return os.urandom(12)

def derive_kek_argon2id(password: str, salt: bytes, length: int = 32,
                        time_cost: int = 3, memory_cost: int = 262144, parallelism: int = 4) -> bytes:
    argon2id = Argon2id(
        salt=salt,
        length=length,
        iterations=time_cost,
        lanes=parallelism,
        memory_cost=memory_cost
    )
    return argon2id.derive(password.encode('utf-8'))

def encrypt_aead(key: bytes, plaintext: bytes, associated_data: bytes) -> tuple[bytes, bytes]:
    aesgcm = AESGCM(key)
    nonce = generate_nonce()
    ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
    return nonce, ciphertext

def decrypt_aead(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes) -> bytes:
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(nonce, ciphertext, associated_data)

def canonicalize_json(data: dict) -> bytes:
    # Uses standard python json module with sort_keys=True and no spaces
    return json.dumps(data, sort_keys=True, separators=(',', ':')).encode('utf-8')
