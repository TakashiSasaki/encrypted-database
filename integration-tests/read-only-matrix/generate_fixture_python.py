import sys
import os
import json
import sqlite3

# Add python src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python/src')))

from encrypted_storage.storage import EncryptedStorage

def main():
    if len(sys.argv) < 3:
        print("Usage: generate_fixture_python.py <db_path> <env_out_path>", file=sys.stderr)
        sys.exit(1)

    db_path = sys.argv[1]
    env_out_path = sys.argv[2]
    passphrase = "fixture-passphrase-python"

    if os.path.exists(db_path):
        os.remove(db_path)

    storage = EncryptedStorage(db_path)
    try:
        storage.initialize_database(passphrase, "linux")

        schema_uuid = "00000000-0000-4000-8000-000000000001"
        content_type = "application/json"
        payload = {
            "secret": "cross-language-fixture",
            "value": 42,
            "nested": {
                "ok": True
            },
            "items": ["python", "go", "rust"]
        }

        obj_uuid = storage.store_payload(schema_uuid, content_type, payload)

        # We need the JCS canonical payload hex to pass to Go/Rust reader tests.
        # The expected_payload_hex MUST strictly be the lowercase hex of the JCS canonical payload bytes.
        import jcs
        canonical_bytes = jcs.canonicalize(payload)
        expected_payload_hex = canonical_bytes.hex()

        with open(env_out_path, 'w') as f:
            f.write(f'VAULT_SQLITE_V1_FIXTURE_DB="{db_path}"\n')
            f.write(f'VAULT_SQLITE_V1_FIXTURE_PASSPHRASE="{passphrase}"\n')
            f.write(f'VAULT_SQLITE_V1_FIXTURE_OBJECT_UUID="{obj_uuid}"\n')
            f.write(f'VAULT_SQLITE_V1_FIXTURE_EXPECTED_PAYLOAD_HEX="{expected_payload_hex}"\n')

    finally:
        storage.close()

if __name__ == "__main__":
    main()
