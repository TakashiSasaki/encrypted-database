import sys
import os
import json

# add python src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python/src')))

from encrypted_storage.storage import EncryptedStorage

def main():
    if len(sys.argv) < 3:
        print("Usage: write_python.py <db_path> <passphrase>")
        sys.exit(1)

    db_path = sys.argv[1]
    passphrase = sys.argv[2]

    storage = EncryptedStorage(db_path)
    try:
        storage.initialize_database(passphrase, "linux")

        schema_uuid = "00000000-0000-4000-8000-000000000001"
        content_type = "application/json"
        payload = {
            "secret": "cross-language",
            "value": 42,
            "nested": {
                "ok": True
            },
            "items": ["python", "nodejs"]
        }

        obj_uuid = storage.store_payload(schema_uuid, content_type, payload)
        print(obj_uuid)
    finally:
        storage.close()

if __name__ == "__main__":
    main()
