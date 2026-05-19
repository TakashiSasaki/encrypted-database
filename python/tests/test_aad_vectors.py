import json
import os
import pytest
from encrypted_storage.aad_policy import build_aad_bytes, build_aad_context, AadPolicyError

def load_aad_vectors():
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'aad', 'aad-basic.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_negative_aad_vectors():
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'test-vectors', 'aad', 'aad-negative.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.mark.parametrize("vector", load_aad_vectors(), ids=lambda v: v["name"])
def test_aad_vectors(vector):
    policy_name = vector["policy"]
    args = vector["args"]
    expected_context = vector["expected_context"]
    expected_string = vector["expected_string"]
    expected_hex = vector["expected_hex"]

    # Verify context building
    actual_context = build_aad_context(policy_name, **args)
    assert actual_context == expected_context

    # Verify canonicalized AAD bytes
    actual_bytes = build_aad_bytes(policy_name, **args)
    assert actual_bytes.hex() == expected_hex
    assert actual_bytes.decode('utf-8') == expected_string

@pytest.mark.parametrize("vector", load_negative_aad_vectors(), ids=lambda v: v["description"])
def test_negative_aad_vectors(vector):
    policy_name = vector["policy"]
    args = vector["args"]
    expected_error = vector["expected_error"]

    with pytest.raises(AadPolicyError) as exc_info:
        build_aad_bytes(policy_name, **args)

    assert expected_error in str(exc_info.value)
