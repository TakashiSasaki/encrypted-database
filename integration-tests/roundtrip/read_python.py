import sys
import os
import json

# add python src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python/src')))

from encrypted_storage.storage import EncryptedStorage

def main():
    if len(sys.argv) < 4:
        print("Usage: read_python.py <db_path> <passphrase> <obj_uuid>", file=sys.stderr)
        sys.exit(1)

    db_path = sys.argv[1]
    passphrase = sys.argv[2]
    obj_uuid = sys.argv[3]

    storage = EncryptedStorage(db_path)
    try:
        storage.unlock_database(passphrase)

        payload = storage.retrieve_payload(obj_uuid)

        expected_payload = {
            "secret": "cross-language",
            "value": 42,
            "nested": {
                "ok": True
            },
            "items": ["python", "nodejs"]
        }

        if payload != expected_payload:
            print(f"Payload mismatch. Expected: {expected_payload}, Got: {payload}", file=sys.stderr)
            sys.exit(1)

        print("PAYLOAD_MATCH_SUCCESS")
    finally:
        storage.close()

if __name__ == "__main__":
    main()
