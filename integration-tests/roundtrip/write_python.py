import sys
import os
import uuid

# add python src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python/src')))

from encrypted_storage.storage import EncryptedStorage

def main():
    db_path = sys.argv[1]
    passphrase = sys.argv[2]

    storage = EncryptedStorage(db_path)
    storage.initialize_database(passphrase, "linux")

    schema_uuid = str(uuid.uuid4())
    content_type = "application/json"
    payload = {"hello": "from python"}

    obj_uuid = storage.store_payload(schema_uuid, content_type, payload)
    print(obj_uuid)

if __name__ == "__main__":
    main()
