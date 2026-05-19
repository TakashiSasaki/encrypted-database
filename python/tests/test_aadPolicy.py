import pytest
from encrypted_storage.aad_policy import select_payload_policy, select_key_wrap_policy, get_policy, AadPolicyError

def test_select_payload_policy():
    assert select_payload_policy() == "record-payload-v1"
    with pytest.raises(AadPolicyError):
        select_payload_policy(alg="unsupported")

def test_select_key_wrap_policy():
    assert select_key_wrap_policy(wrapped_key_class="database_kek") == "wrap-database-key-v1"
    assert select_key_wrap_policy(wrapped_key_class="record_dek") == "wrap-record-key-v1"
    assert select_key_wrap_policy(wrapped_key_class="file_dek") == "wrap-record-key-v1"
    with pytest.raises(AadPolicyError):
        select_key_wrap_policy(wrapped_key_class="unknown")
    with pytest.raises(AadPolicyError):
        select_key_wrap_policy(wrapped_key_class="record_dek", alg="unsupported")

def test_get_policy_unknown():
    with pytest.raises(AadPolicyError):
        get_policy("unknown")
