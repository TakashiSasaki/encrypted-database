import sqlite3
import json
import sys
import os

# Ensure the library can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../python/src')))

from encrypted_storage.storage import EncryptedStorage

def main():
    if len(sys.argv) < 2:
        print("Usage: python create_python_db.py <db_path>")
        sys.exit(1)

    db_path = sys.argv[1]

    if os.path.exists(db_path):
        os.remove(db_path)

    storage = EncryptedStorage(db_path)
    conn = storage.conn

    with open(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../docs/backend/sqlite/schema.sql')), 'r') as f:
        schema_sql = f.read()
    conn.executescript(schema_sql)

    # Pre-populate platform table as per schema requirements
    conn.execute("INSERT INTO platform_tbl (platform, description) VALUES ('integration_test_platform', 'Integration Test Platform')")
    conn.commit()

    storage.initialize_database("fixed_passphrase", "integration_test_platform")

    payload = {"hello": "world", "source": "python"}
    schema_uuid = "00000000-0000-4000-8000-000000000001"

    object_uuid = storage.store_payload(schema_uuid, "application/json", payload)

    # Print the UUID to stdout so it can be captured
    print(object_uuid)

    storage.close()

if __name__ == "__main__":
    main()
