import sys
import json
import argparse
import os

from encrypted_storage.storage import EncryptedStorage
from encrypted_storage import errors

def main():
    parser = argparse.ArgumentParser(description="Test-only compatibility wrapper")
    parser.add_argument("operation", choices=["write", "read"])
    parser.add_argument("--db", required=True)
    parser.add_argument("--schema", required=True)
    parser.add_argument("--content-type", dest="content_type", required=True)
    parser.add_argument("--object-uuid", dest="object_uuid", required=False) # Only needed for read but passed from write

    args = parser.parse_args()

    passphrase = os.environ.get("VAULT_PASSPHRASE")
    if not passphrase:
        print(json.dumps({"ok": False, "operation": args.operation, "error": "VAULT_PASSPHRASE environment variable is required"}))
        sys.exit(1)

    try:
        storage = EncryptedStorage(args.db)

        if args.operation == "write":
            if storage.get_status() == "uninitialized":
                storage.initialize_database(passphrase, "linux") # Using "linux" as dummy platform for tests
            else:
                storage.unlock_database(passphrase)

            payload_str = sys.stdin.read()
            payload = json.loads(payload_str)

            object_uuid = storage.store_payload(args.schema, args.content_type, payload)

            storage.close()

            print(json.dumps({
                "ok": True,
                "operation": "write",
                "object_uuid": object_uuid
            }))

        elif args.operation == "read":
            if not args.object_uuid:
                print(json.dumps({"ok": False, "operation": "read", "error": "--object-uuid is required for read operation"}))
                sys.exit(1)

            storage.unlock_database(passphrase)
            payload = storage.retrieve_payload(args.object_uuid)
            storage.close()

            print(json.dumps({
                "ok": True,
                "operation": "read",
                "payload": payload
            }))

    except errors.Error as e:
        print(json.dumps({
            "ok": False,
            "operation": args.operation,
            "error": str(e)
        }))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "operation": args.operation,
            "error": str(e)
        }))
        sys.exit(1)

if __name__ == "__main__":
    main()
