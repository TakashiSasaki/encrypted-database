import sqlite3
import time
import uuid
import json
import base64
from pathlib import Path

from . import crypto

class EncryptedStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()
        self.active_db_kek = None
        self.active_db_kid = None
        self.active_db_kid = None

    def _init_db(self):
        schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        self.conn.executescript(schema_sql)
        self.conn.commit()

    def _generate_kid(self) -> str:
        return str(uuid.uuid4())

    def _current_ms(self) -> int:
        return int(time.time() * 1000)

    def _b64e(self, b: bytes) -> str:
        return base64.urlsafe_b64encode(b).decode('utf-8').rstrip('=')

    def _b64d(self, s: str) -> bytes:
        pad = b'=' * (4 - (len(s) % 4))
        return base64.urlsafe_b64decode(s.encode('utf-8') + pad)

    def initialize_database(self, passphrase: str, platform: str = "cross_platform"):
        """Initializes a new database with a new database_kek wrapped by a new unlock_kek."""
        db_kek_bytes = crypto.generate_random_bytes(32)
        db_kid = self._generate_kid()

        # Save db_kek info
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (db_kid, 'database_kek', 'wrap_record_keys', 'A256GCM', 'active', self._current_ms())
        )

        # Derive unlock KEK
        salt = crypto.generate_random_bytes(16)
        time_cost = 3
        memory_cost = 262144
        parallelism = 4

        unlock_kek_bytes = crypto.derive_kek_argon2id(passphrase, salt, 32, time_cost, memory_cost, parallelism)
        unlock_kid = self._generate_kid()

        cur.execute(
            "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (unlock_kid, 'unlock_kek', 'wrap_database_keys', 'A256GCM', 'active', self._current_ms())
        )

        provider_config = {
            "salt": self._b64e(salt),
            "memory_kib": memory_cost,
            "iterations": time_cost,
            "parallelism": parallelism
        }

        cur.execute(
            "INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)",
            (unlock_kid, 'passphrase_argon2id', json.dumps(provider_config), platform)
        )

        # Wrap database KEK with unlock KEK
        aad_context = {
            "v": 1,
            "aad_policy": "wrap-database-key-v1",
            "wrapped_kid": db_kid,
            "wrapping_kid": unlock_kid
        }
        aad_bytes = crypto.canonicalize_json(aad_context)
        nonce, wrapped_db_kek = crypto.encrypt_aead(unlock_kek_bytes, db_kek_bytes, aad_bytes)

        cur.execute(
            "INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (db_kid, unlock_kid, 'A256GCM', nonce, wrapped_db_kek, crypto.canonicalize_json(aad_context).decode('utf-8'), self._current_ms())
        )

        self.conn.commit()
        self.active_db_kek = db_kek_bytes
        self.active_db_kid = db_kid

    def unlock_database(self, passphrase: str):
        """Unlocks the database by retrieving and unwrapping the database_kek."""
        cur = self.conn.cursor()

        # Find active database KEK
        cur.execute("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1")
        row = cur.fetchone()
        if not row:
            raise ValueError("No active database KEK found")
        db_kid = row[0]

        # Get wrap info
        cur.execute("SELECT wrapping_kid, nonce, wrapped_key, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ?", (db_kid,))
        wrap_rows = cur.fetchall()

        unwrapped = False
        for wrapping_kid, nonce, wrapped_key, aad_context_json in wrap_rows:
            cur.execute("SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?", (wrapping_kid,))
            prov_row = cur.fetchone()
            if prov_row and prov_row[0] == 'passphrase_argon2id':
                config = json.loads(prov_row[1])
                salt = self._b64d(config['salt'])
                try:
                    unlock_kek_bytes = crypto.derive_kek_argon2id(
                        passphrase, salt, 32, config['iterations'], config['memory_kib'], config['parallelism']
                    )
                    db_kek_bytes = crypto.decrypt_aead(unlock_kek_bytes, nonce, wrapped_key, aad_context_json.encode('utf-8'))
                    self.active_db_kek = db_kek_bytes
                    self.active_db_kid = db_kid
                    unwrapped = True
                    break
                except Exception:
                    continue

        if not unwrapped:
            raise ValueError("Failed to unlock database")

    def store_payload(self, schema_uuid: str, content_type: str, payload: dict) -> str:
        """Encrypts and stores a JSON payload."""
        if not self.active_db_kek:
            raise ValueError("Database is locked")

        object_uuid = self._generate_kid()

        # 1. Generate record DEK
        record_dek_bytes = crypto.generate_random_bytes(32)
        record_kid = self._generate_kid()

        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (record_kid, 'record_dek', 'encrypt_payload', 'A256GCM', 'active', self._current_ms())
        )

        # 2. Wrap record DEK with database KEK
        wrap_aad = {
            "v": 1,
            "aad_policy": "wrap-record-key-v1",
            "wrapped_kid": record_kid,
            "wrapping_kid": self.active_db_kid
        }
        wrap_aad_bytes = crypto.canonicalize_json(wrap_aad)
        nonce_wrap, wrapped_record_dek = crypto.encrypt_aead(self.active_db_kek, record_dek_bytes, wrap_aad_bytes)

        cur.execute(
            "INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (record_kid, self.active_db_kid, 'A256GCM', nonce_wrap, wrapped_record_dek, wrap_aad_bytes.decode('utf-8'), self._current_ms())
        )

        # 3. Encrypt payload with record DEK
        payload_bytes = crypto.canonicalize_json(payload)
        payload_aad = {
            "v": 1,
            "aad_policy": "record-payload-v1",
            "object_uuid": object_uuid,
            "schema_uuid": schema_uuid,
            "content_type": content_type,
            "kid": record_kid,
            "alg": "A256GCM"
        }
        payload_aad_bytes = crypto.canonicalize_json(payload_aad)
        nonce_payload, ciphertext = crypto.encrypt_aead(record_dek_bytes, payload_bytes, payload_aad_bytes)

        cur.execute(
            "INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (object_uuid, schema_uuid, content_type, 'A256GCM', record_kid, nonce_payload, ciphertext, 'record-payload-v1', self._current_ms(), self._current_ms())
        )

        self.conn.commit()
        return object_uuid

    def retrieve_payload(self, object_uuid: str) -> dict:
        """Retrieves and decrypts a payload."""
        if not self.active_db_kek:
            raise ValueError("Database is locked")

        cur = self.conn.cursor()
        cur.execute("SELECT schema_uuid, content_type, kid, nonce, ciphertext FROM encrypted_object_tbl WHERE object_uuid = ?", (object_uuid,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Object not found")

        schema_uuid, content_type, record_kid, nonce_payload, ciphertext = row

        # Get wrapped record DEK
        cur.execute("SELECT nonce, wrapped_key, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?", (record_kid, self.active_db_kid))
        wrap_row = cur.fetchone()
        if not wrap_row:
            raise ValueError("Record DEK wrap info not found")

        nonce_wrap, wrapped_record_dek, aad_context_json_wrap = wrap_row

        # Unwrap record DEK
        record_dek_bytes = crypto.decrypt_aead(self.active_db_kek, nonce_wrap, wrapped_record_dek, aad_context_json_wrap.encode('utf-8'))

        # Decrypt payload
        payload_aad = {
            "v": 1,
            "aad_policy": "record-payload-v1",
            "object_uuid": object_uuid,
            "schema_uuid": schema_uuid,
            "content_type": content_type,
            "kid": record_kid,
            "alg": "A256GCM"
        }
        payload_aad_bytes = crypto.canonicalize_json(payload_aad)

        payload_bytes = crypto.decrypt_aead(record_dek_bytes, nonce_payload, ciphertext, payload_aad_bytes)
        return json.loads(payload_bytes.decode('utf-8'))

    def close(self):
        self.conn.close()
        self.active_db_kek = None
        self.active_db_kid = None
