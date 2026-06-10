import sys
import os
import json

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
    if len(sys.argv) < 8:
        print("Usage: python write_matrix_fixture_python.py <db_path> <passphrase> <platform> <schema_uuid> <content_type> <payload_a_json> <payload_b_json> [mode:update_only|update_delete]", file=sys.stderr)
        sys.exit(1)

    db_path = sys.argv[1]
    passphrase = sys.argv[2]
    platform = sys.argv[3]
    schema_uuid = sys.argv[4]
    content_type = sys.argv[5]
    payload_a_json = sys.argv[6]
    payload_b_json = sys.argv[7]

    mode = "update_delete"
    if len(sys.argv) >= 9:
        mode = sys.argv[8]

    if mode not in ["update_only", "update_delete"]:
        print(f"Error: Invalid mode '{mode}'. Allowed modes are 'update_only' and 'update_delete'.", file=sys.stderr)
        sys.exit(1)

    # V1 Writers from python/node ignore VAULT_SCHEMA_SQL_PATH normally, so we don't read it here.

    if os.path.exists(db_path):
        print(f"Error: Database file already exists at {db_path}", file=sys.stderr)
        sys.exit(1)

    try:
        payload_a = json.loads(payload_a_json)
        payload_b = json.loads(payload_b_json)
    except Exception as e:
        print(f"Error parsing JSON payload: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        storage = EncryptedStorage(db_path)
        storage.initialize_database(passphrase, platform)

        object_uuid = storage.store_payload(schema_uuid, content_type, payload_a)
        storage.update_payload(object_uuid, schema_uuid, content_type, payload_b)

        deleted = False
        if mode == "update_delete":
            storage.delete_payload(object_uuid)
            deleted = True

        # output jcs canonical hex for A and B
        initial_hex = canonicalize_json(payload_a).hex().lower()
        updated_hex = canonicalize_json(payload_b).hex().lower()

        output = {
            "object_uuid": object_uuid,
            "initial_payload_hex": initial_hex,
            "updated_payload_hex": updated_hex,
            "deleted": deleted
        }

        print(json.dumps(output))

    except Exception as e:
        print(f"Error during Python write: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
