import json
import os
import pytest
from encrypted_storage.crypto import canonicalize_json

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), "testdata")
INPUT_DIR = os.path.join(TESTDATA_DIR, "input")
OUTPUT_DIR = os.path.join(TESTDATA_DIR, "output")

def get_test_vectors():
    vectors = []
    if not os.path.isdir(INPUT_DIR):
        raise pytest.UsageError(f"Required test vector input directory is missing: {INPUT_DIR}")

    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".json"):
            vectors.append(filename)

    if not vectors:
        raise pytest.UsageError(f"No JSON test vectors found in: {INPUT_DIR}")

    return vectors

@pytest.mark.parametrize("filename", get_test_vectors())
def test_rfc8785_canonicalization(filename):
    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)

    with open(input_path, "r", encoding="utf-8") as f:
        # Some RFC 8785 vectors might be simple arrays or numbers, but here we load as standard JSON.
        data = json.load(f)

    with open(output_path, "rb") as f:
        expected_output = f.read()

    # The original canonicalize_json returns bytes
    canonicalized = canonicalize_json(data)

    assert canonicalized == expected_output, f"Failed canonicalization for {filename}"
