import pytest
import sqlite3
import json
import base64
from encrypted_storage.storage import EncryptedStorage

def test_sql_constraints(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    conn.execute("PRAGMA foreign_keys = ON")

    cur.execute("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' LIMIT 1")
    db_kid = cur.fetchone()[0]

    object_uuid = "12345678-1234-4234-8234-123456789012"

    # 1. encrypted_object_tbl.nonce 12 bytes
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)",
            (object_uuid, object_uuid, 1, "aead", "application/json", "A256GCM", db_kid, b"shortnonce", b"x"*16, "none", ))

    # 2. encrypted_object_tbl.ciphertext >= 16 bytes
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)",
            (object_uuid, object_uuid, 1, "aead", "application/json", "A256GCM", db_kid, b"n"*12, b"short", "none", ))

    # 3. encrypted_object_tbl.content_type empty string
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)",
            (object_uuid, object_uuid, 1, "aead", "", "A256GCM", db_kid, b"n"*12, b"x"*16, "none", ))

    # 4. encrypted_object_tbl.content_type no slash
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, envelope_v, envelope_type, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 123, 123)",
            (object_uuid, object_uuid, 1, "aead", "noslash", "A256GCM", db_kid, b"n"*12, b"x"*16, "none", ))

    # 5. wrapped_key_tbl.nonce 12 bytes
    wrap_id = "00000000-0000-4000-8000-000000000000"
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (wrap_id, db_kid, db_kid, 1, "key_wrap", "A256GCM", b"shortnonce", b"x"*32, "policy", 123))

    # 6. wrapped_key_tbl.wrapped_key >= 16 bytes
    with pytest.raises(sqlite3.IntegrityError):
        cur.execute("INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (wrap_id, db_kid, db_kid, 1, "key_wrap", "A256GCM", b"n"*12, b"short", "policy", 123))
