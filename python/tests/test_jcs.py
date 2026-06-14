import json
import os
import pytest
from encrypted_storage.crypto import canonicalize_json

def load_jcs_vectors():
    vectors = []
    files = ['rfc8785-basic.json', 'generic-positive-coverage.json']
    for file_name in files:
        path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'jcs', file_name)
        with open(path, 'r', encoding='utf-8') as f:
            file_vectors = json.load(f)
            # Add file name to the vector for better error reporting and test IDs
            for v in file_vectors:
                v['_file'] = file_name
            vectors.extend(file_vectors)
    return vectors

@pytest.mark.parametrize("vector", load_jcs_vectors(), ids=lambda v: f"{v['_file']}:{v['name']}")
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
