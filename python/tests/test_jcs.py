import json
import os
import pytest
from encrypted_storage.crypto import canonicalize_json

def load_jcs_vectors():
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'jcs', 'rfc8785-basic.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.mark.parametrize("vector", load_jcs_vectors(), ids=lambda v: v["name"])
def test_jcs_canonicalization(vector):
    input_data = vector["input"]
    expected_string = vector["expected_string"]
    expected_hex = vector["expected_hex"]

    # Canonicalize
    actual_bytes = canonicalize_json(input_data)

    # Verify byte-for-byte correctness (hex)
    assert actual_bytes.hex() == expected_hex

    # Verify string equivalence
    assert actual_bytes.decode('utf-8') == expected_string
