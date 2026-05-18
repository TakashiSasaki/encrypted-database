import sqlite3
import time
import uuid
import json
import base64
from pathlib import Path

from . import aad_policy
from . import crypto

class EncryptedStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()
        self.active_db_kek = None
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

    def _validate_platform(self, platform: str):
        if not platform or platform == "cross_platform":
            raise ValueError("A concrete platform name is required; cross_platform is not allowed")
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM platform_tbl WHERE platform = ?", (platform,))
        if not cur.fetchone():
            raise ValueError(f"Unsupported platform: {platform}")

    def initialize_database(self, passphrase: str, platform: str):
        """Initializes a new database with a new database_kek wrapped by a new unlock_kek."""
        self._validate_platform(platform)

        db_kek_bytes = crypto.generate_random_bytes(32)
        db_kid = self._generate_kid()

        # Derive unlock KEK
        salt = crypto.generate_random_bytes(16)
        time_cost = 3
        memory_cost = 262144
        parallelism = 4

        unlock_kek_bytes = crypto.derive_kek_argon2id(passphrase, salt, 32, time_cost, memory_cost, parallelism)
        unlock_kid = self._generate_kid()

        provider_config = {
            "salt": self._b64e(salt),
            "memory_kib": memory_cost,
            "iterations": time_cost,
            "parallelism": parallelism
        }

        # Wrap database KEK with unlock KEK. The library selects the AAD policy
        # from the operation and wrapped key class; callers do not provide it.
        wrap_alg = "A256GCM"
        aad_policy_name = aad_policy.select_key_wrap_policy(wrapped_key_class="database_kek", alg=wrap_alg)
        aad_context = aad_policy.build_aad_context(
            aad_policy_name,
            wrapped_kid=db_kid,
            wrapping_kid=unlock_kid,
        )
        aad_bytes = aad_policy.build_aad_bytes(
            aad_policy_name,
            wrapped_kid=db_kid,
            wrapping_kid=unlock_kid,
        )
        nonce, wrapped_db_kek = crypto.encrypt_aead(unlock_kek_bytes, db_kek_bytes, aad_bytes)

        cur = self.conn.cursor()
        cur.execute("BEGIN TRANSACTION")
        try:
            # Save db_kek info
            cur.execute(
                "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (db_kid, 'database_kek', 'wrap_record_keys', wrap_alg, 'active', self._current_ms())
            )
            cur.execute(
                "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (unlock_kid, 'unlock_kek', 'wrap_database_keys', wrap_alg, 'active', self._current_ms())
            )
            cur.execute(
                "INSERT INTO unlock_kek_tbl (kid, unlock_provider, provider_config_json, created_on_platform) VALUES (?, ?, ?, ?)",
                (unlock_kid, 'passphrase_argon2id', crypto.canonicalize_json(provider_config).decode('utf-8'), platform)
            )
            cur.execute(
                "INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_policy, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (db_kid, unlock_kid, wrap_alg, nonce, wrapped_db_kek, aad_policy_name, crypto.canonicalize_json(aad_context).decode('utf-8'), self._current_ms())
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

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
        cur.execute("SELECT wrapping_kid, nonce, wrapped_key, aad_policy, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ?", (db_kid,))
        wrap_rows = cur.fetchall()

        unwrapped = False
        for wrapping_kid, nonce, wrapped_key, aad_policy_name, aad_context_json in wrap_rows:
            try:
                aad_policy.get_policy(aad_policy_name)
            except aad_policy.AadPolicyError:
                continue

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
                except Exception as e:
                    # In a real implementation we might want to log or be more specific
                    # based on cryptography's InvalidTag exceptions
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
        alg = "A256GCM"

        # 2. Wrap record DEK with database KEK
        wrap_aad_policy = aad_policy.select_key_wrap_policy(wrapped_key_class="record_dek", alg=alg)
        wrap_aad = aad_policy.build_aad_context(
            wrap_aad_policy,
            wrapped_kid=record_kid,
            wrapping_kid=self.active_db_kid,
        )
        wrap_aad_bytes = aad_policy.build_aad_bytes(
            wrap_aad_policy,
            wrapped_kid=record_kid,
            wrapping_kid=self.active_db_kid,
        )
        nonce_wrap, wrapped_record_dek = crypto.encrypt_aead(self.active_db_kek, record_dek_bytes, wrap_aad_bytes)

        # 3. Encrypt payload with record DEK
        payload_bytes = crypto.canonicalize_json(payload)
        payload_aad_policy = aad_policy.select_payload_policy(alg=alg)
        payload_aad = aad_policy.build_aad_context(
            payload_aad_policy,
            object_uuid=object_uuid,
            schema_uuid=schema_uuid,
            content_type=content_type,
            kid=record_kid,
            alg=alg,
        )
        payload_aad_bytes = aad_policy.build_aad_bytes(
            payload_aad_policy,
            object_uuid=object_uuid,
            schema_uuid=schema_uuid,
            content_type=content_type,
            kid=record_kid,
            alg=alg,
        )
        nonce_payload, ciphertext = crypto.encrypt_aead(record_dek_bytes, payload_bytes, payload_aad_bytes)

        cur = self.conn.cursor()
        cur.execute("BEGIN TRANSACTION")
        try:
            cur.execute(
                "INSERT INTO key_tbl (kid, key_class, purpose, alg, status, created_at_ms) VALUES (?, ?, ?, ?, ?, ?)",
                (record_kid, 'record_dek', 'encrypt_payload', alg, 'active', self._current_ms())
            )
            cur.execute(
                "INSERT INTO wrapped_key_tbl (wrapped_kid, wrapping_kid, wrap_alg, nonce, wrapped_key, aad_policy, aad_context_json, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (record_kid, self.active_db_kid, alg, nonce_wrap, wrapped_record_dek, wrap_aad_policy, crypto.canonicalize_json(wrap_aad).decode('utf-8'), self._current_ms())
            )
            cur.execute(
                "INSERT INTO encrypted_object_tbl (object_uuid, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (object_uuid, schema_uuid, content_type, alg, record_kid, nonce_payload, ciphertext, payload_aad_policy, self._current_ms(), self._current_ms())
            )
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

        return object_uuid

    def retrieve_payload(self, object_uuid: str) -> dict:
        """Retrieves and decrypts a payload."""
        if not self.active_db_kek:
            raise ValueError("Database is locked")

        cur = self.conn.cursor()
        cur.execute("SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?", (object_uuid,))
        row = cur.fetchone()
        if not row:
            raise ValueError("Object not found")

        schema_uuid, content_type, alg, record_kid, nonce_payload, ciphertext, payload_aad_policy = row
        aad_policy.get_policy(payload_aad_policy)

        # Get wrapped record DEK
        cur.execute("SELECT nonce, wrapped_key, aad_policy, aad_context_json FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?", (record_kid, self.active_db_kid))
        wrap_row = cur.fetchone()
        if not wrap_row:
            raise ValueError("Record DEK wrap info not found")

        nonce_wrap, wrapped_record_dek, wrap_aad_policy, aad_context_json_wrap = wrap_row
        aad_policy.get_policy(wrap_aad_policy)

        # Unwrap record DEK
        record_dek_bytes = crypto.decrypt_aead(self.active_db_kek, nonce_wrap, wrapped_record_dek, aad_context_json_wrap.encode('utf-8'))

        # Decrypt payload using the registered policy saved with the object.
        payload_aad_bytes = aad_policy.build_aad_bytes(
            payload_aad_policy,
            object_uuid=object_uuid,
            schema_uuid=schema_uuid,
            content_type=content_type,
            kid=record_kid,
            alg=alg,
        )

        payload_bytes = crypto.decrypt_aead(record_dek_bytes, nonce_payload, ciphertext, payload_aad_bytes)
        return json.loads(payload_bytes.decode('utf-8'))

    def close(self):
        self.conn.close()
        self.active_db_kek = None
        self.active_db_kid = None
