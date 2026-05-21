from dataclasses import dataclass
from typing import Any, Callable, Dict

from . import crypto


from .errors import AadPolicyError



@dataclass(frozen=True)
class AadPolicy:
    name: str
    envelope_type: str
    build_context: Callable[..., Dict[str, Any]]

    def context(self, **kwargs: Any) -> Dict[str, Any]:
        return self.build_context(**kwargs)

    def aad_bytes(self, **kwargs: Any) -> bytes:
        # crypto.canonicalize_json is the canonicalization boundary.
        # This implementation uses an RFC 8785 JCS compliant library,
        # which is verified against the shared cross-language test vectors.
        return crypto.canonicalize_json(self.context(**kwargs))


RECORD_PAYLOAD_V1 = "record-payload-v1"
WRAP_DATABASE_KEY_V1 = "wrap-database-key-v1"
WRAP_RECORD_KEY_V1 = "wrap-record-key-v1"


def _record_payload_v1_context(*, object_uuid: str = None, schema_uuid: str = None, content_type: str = None, kid: str = None, alg: str = None, **kwargs: Any) -> Dict[str, Any]:
    if not object_uuid: raise AadPolicyError("Missing required field: object_uuid")
    if not schema_uuid: raise AadPolicyError("Missing required field: schema_uuid")
    if not content_type: raise AadPolicyError("Missing required field: content_type")
    if not kid: raise AadPolicyError("Missing required field: kid")
    if not alg: raise AadPolicyError("Missing required field: alg")
    return {
        "v": 1,
        "aad_policy": RECORD_PAYLOAD_V1,
        "object_uuid": object_uuid,
        "schema_uuid": schema_uuid,
        "content_type": content_type,
        "kid": kid,
        "alg": alg,
    }


def _wrap_database_key_v1_context(*, wrapped_kid: str = None, wrapping_kid: str = None, **kwargs: Any) -> Dict[str, Any]:
    if not wrapped_kid: raise AadPolicyError("Missing required field: wrapped_kid")
    if not wrapping_kid: raise AadPolicyError("Missing required field: wrapping_kid")
    return {
        "v": 1,
        "aad_policy": WRAP_DATABASE_KEY_V1,
        "wrapped_kid": wrapped_kid,
        "wrapping_kid": wrapping_kid,
    }


def _wrap_record_key_v1_context(*, wrapped_kid: str = None, wrapping_kid: str = None, **kwargs: Any) -> Dict[str, Any]:
    if not wrapped_kid: raise AadPolicyError("Missing required field: wrapped_kid")
    if not wrapping_kid: raise AadPolicyError("Missing required field: wrapping_kid")
    return {
        "v": 1,
        "aad_policy": WRAP_RECORD_KEY_V1,
        "wrapped_kid": wrapped_kid,
        "wrapping_kid": wrapping_kid,
    }


AAD_POLICY_REGISTRY: Dict[str, AadPolicy] = {
    RECORD_PAYLOAD_V1: AadPolicy(
        name=RECORD_PAYLOAD_V1,
        envelope_type="aead",
        build_context=_record_payload_v1_context,
    ),
    WRAP_DATABASE_KEY_V1: AadPolicy(
        name=WRAP_DATABASE_KEY_V1,
        envelope_type="key_wrap",
        build_context=_wrap_database_key_v1_context,
    ),
    WRAP_RECORD_KEY_V1: AadPolicy(
        name=WRAP_RECORD_KEY_V1,
        envelope_type="key_wrap",
        build_context=_wrap_record_key_v1_context,
    ),
}


def get_policy(policy_name: str) -> AadPolicy:
    try:
        return AAD_POLICY_REGISTRY[policy_name]
    except KeyError as exc:
        raise AadPolicyError(f"Unknown AAD policy: {policy_name}") from exc


def build_aad_context(policy_name: str, **kwargs: Any) -> Dict[str, Any]:
    return get_policy(policy_name).context(**kwargs)


def build_aad_bytes(policy_name: str, **kwargs: Any) -> bytes:
    return get_policy(policy_name).aad_bytes(**kwargs)


def select_payload_policy(*, envelope_v: int = 1, envelope_type: str = "aead", alg: str = "A256GCM") -> str:
    if envelope_v == 1 and envelope_type == "aead" and alg == "A256GCM":
        return RECORD_PAYLOAD_V1
    raise AadPolicyError(
        f"No registered payload AAD policy for envelope_v={envelope_v}, "
        f"envelope_type={envelope_type}, alg={alg}"
    )


def select_key_wrap_policy(*, wrapped_key_class: str, envelope_v: int = 1, envelope_type: str = "key_wrap", alg: str = "A256GCM") -> str:
    if envelope_v != 1 or envelope_type != "key_wrap" or alg != "A256GCM":
        raise AadPolicyError(
            f"No registered key-wrap AAD policy for envelope_v={envelope_v}, "
            f"envelope_type={envelope_type}, alg={alg}"
        )

    if wrapped_key_class == "database_kek":
        return WRAP_DATABASE_KEY_V1
    if wrapped_key_class in {"record_dek", "file_dek"}:
        return WRAP_RECORD_KEY_V1

    raise AadPolicyError(f"No registered key-wrap AAD policy for wrapped_key_class={wrapped_key_class}")
