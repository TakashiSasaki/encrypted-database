import sys
import os
import json
import sqlite3

# Add python source to path so we can import encrypted_storage without installation if needed,
# though pip install -e .[test] is expected.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python/src'))

try:
    from encrypted_storage import EncryptedStorage
    from encrypted_storage.crypto import canonicalize_json
except ImportError as e:
    print(f"Error: Python dependencies not met. Run 'pip install -e .[test]' in python/. Details: {e}", file=sys.stderr)
    sys.exit(1)

def main():
    if len(sys.argv) != 4:
        print("Usage: python read_fixture_python.py <db_path> <passphrase> <object_uuid>", file=sys.stderr)
        sys.exit(1)

    db_path = sys.argv[1]
    passphrase = sys.argv[2]
    object_uuid = sys.argv[3]

    try:
        storage = EncryptedStorage(db_path)
        storage.unlock_database(passphrase)

        try:
            payload = storage.retrieve_payload(object_uuid)
            not_found = False
        except Exception as e:
            if type(e).__name__ == "ObjectNotFound" or "Object not found" in str(e):
                payload = None
                not_found = True
            else:
                raise e

        output = {
            "object_uuid": object_uuid,
            "not_found": not_found
        }

        if payload is not None:
            # JCS canonicalize the payload to ensure accurate hex comparison
            canonical_bytes = canonicalize_json(payload)
            payload_hex = canonical_bytes.hex().lower()
            output["payload_hex"] = payload_hex

        print(json.dumps(output))
    except Exception as e:
        print(f"Error during Python read: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
