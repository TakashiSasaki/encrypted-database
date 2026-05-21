import sqlite3
import json
import sys
import os

# Ensure the library can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python/src')))

from encrypted_storage.storage import EncryptedStorage

def main():
    if len(sys.argv) < 3:
        print("Usage: python read_with_python.py <db_path> <object_uuid>")
        sys.exit(1)

    db_path = sys.argv[1]
    object_uuid = sys.argv[2]

    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        sys.exit(1)

    storage = EncryptedStorage(db_path)

    storage.unlock_database("fixed_passphrase")

    payload = storage.retrieve_payload(object_uuid)

    if payload.get("hello") == "world" and payload.get("source") == "nodejs":
        print("SUCCESS")
    else:
        print("Payload mismatch:", payload)
        sys.exit(1)

    storage.close()

if __name__ == "__main__":
    main()
