import json
import os
import binascii
from encrypted_storage import crypto

def test_kdf_vectors():
    vectors_path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'kdf', 'argon2id-v1.json')
    with open(vectors_path, 'r') as f:
        vectors = json.load(f)

    for v in vectors:
        if v.get('kdf') != 'argon2id':
            continue

        passphrase = v['passphrase']
        salt_hex = v['salt_hex']
        salt = binascii.unhexlify(salt_hex)
        length = v['length']
        time_cost = v['time_cost']
        memory_cost = v['memory_kib']
        parallelism = v['parallelism']
        expected_hex = v['expected_kek_hex'].lower()

        derived = crypto.derive_kek_argon2id(
            password=passphrase,
            salt=salt,
            length=length,
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism
        )

        assert binascii.hexlify(derived).decode('ascii') == expected_hex, f"KDF vector '{v['name']}' failed"
