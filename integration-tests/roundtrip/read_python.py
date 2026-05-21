import sys
import os

# add python src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python/src')))

from encrypted_storage.storage import EncryptedStorage

def main():
    db_path = sys.argv[1]
    passphrase = sys.argv[2]
    obj_uuid = sys.argv[3]

    storage = EncryptedStorage(db_path)
    storage.unlock_database(passphrase)

    payload = storage.retrieve_payload(obj_uuid)
    # output json string for bash
    import json
    print(json.dumps(payload))

if __name__ == "__main__":
    main()
