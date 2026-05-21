import json
import base64
from cryptography.hazmat.primitives.kdf.argon2 import Argon2id

passphrase = "test-passphrase-123"
# 16 bytes deterministic salt
salt_bytes = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"

argon2id = Argon2id(
    salt=salt_bytes,
    length=32,
    iterations=3,
    lanes=1,
    memory_cost=65536
)

derived_key = argon2id.derive(passphrase.encode('utf-8'))

vector = {
    "profile": "argon2id-profile-v1",
    "description": "Standard cross-platform Argon2id profile for database unlocking",
    "parameters": {
        "memory_kib": 65536,
        "iterations": 3,
        "parallelism": 1,
        "salt_bytes": 16,
        "output_bytes": 32
    },
    "input": {
        "passphrase": passphrase,
        "salt_hex": salt_bytes.hex()
    },
    "expected_output_hex": derived_key.hex()
}

with open("test-vectors/kdf/argon2id-v1.json", "w") as f:
    json.dump([vector], f, indent=2)

print("Test vector generated in test-vectors/kdf/argon2id-v1.json")
