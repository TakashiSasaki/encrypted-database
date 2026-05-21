import sqlite3
import time
import uuid
import json
import base64
from pathlib import Path

from . import aad_policy, crypto, errors

class EncryptedStorage:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.execute("PRAGMA foreign_keys = ON")
        self._init_db()
        self.active_db_kek = None
        self.active_db_kid = None
        self._is_closed = False

    def _init_db(self):
        schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "backend" / "sqlite" / "schema.sql"
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
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")
        if not platform or platform == "cross_platform":
            raise errors.UnsupportedPlatform("A concrete platform name is required; cross_platform is not allowed")
        cur = self.conn.cursor()
        try:
            cur.execute("SELECT 1 FROM platform_tbl WHERE platform = ?", (platform,))
        except sqlite3.Error as e:
            if "no such table" in str(e):
                raise errors.UnsupportedPlatform(f"Unsupported platform: {platform}")
            raise errors.DatabaseBackendError(f"Database error during platform validation: {e}") from e

        if not cur.fetchone():
            raise errors.UnsupportedPlatform(f"Unsupported platform: {platform}")

    def initialize_database(self, passphrase: str, platform: str):
        """Initializes a new database with a new database_kek wrapped by a new unlock_kek."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")
        if self.is_unlocked():
            raise errors.StorageAlreadyInitialized("Storage is already initialized")
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' LIMIT 1")
            if cur.fetchone():
                raise errors.StorageAlreadyInitialized("Storage is already initialized")
        except sqlite3.OperationalError:
            pass
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
            wrap_id = self._generate_kid()
            cur.execute(
                "INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (wrap_id, db_kid, unlock_kid, 1, 'key_wrap', wrap_alg, nonce, wrapped_db_kek, aad_policy_name, self._current_ms())
            )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise errors.DatabaseBackendError(f"Database error during initialization: {e}") from e
        except Exception as e:
            self.conn.rollback()
            raise e

        self.active_db_kek = db_kek_bytes
        self.active_db_kid = db_kid

    def unlock_database(self, passphrase: str):
        """Unlocks the database by retrieving and unwrapping the database_kek."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")
        if not self.conn:
            raise errors.StorageNotInitialized("Database not initialized")
        cur = self.conn.cursor()

        try:
            # Find active database KEK
            cur.execute("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1")
            row = cur.fetchone()
            if not row:
                raise errors.StorageNotInitialized("No active database KEK found")
            db_kid = row[0]

            # Get wrap info
            cur.execute("SELECT wrapping_kid, nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ?", (db_kid,))
            wrap_rows = cur.fetchall()
        except sqlite3.Error as e:
            raise errors.DatabaseBackendError(f"Database error during unlock: {e}") from e

        unwrapped = False
        for wrapping_kid, nonce, wrapped_key, aad_policy_name in wrap_rows:
            try:
                aad_policy.get_policy(aad_policy_name)
            except aad_policy.AadPolicyError:
                continue

            try:
                cur.execute("SELECT unlock_provider, provider_config_json FROM unlock_kek_tbl WHERE kid = ?", (wrapping_kid,))
                prov_row = cur.fetchone()
            except sqlite3.Error as e:
                raise errors.DatabaseBackendError(f"Database error during unlock configuration retrieval: {e}") from e

            if prov_row and prov_row[0] == 'passphrase_argon2id':
                config = json.loads(prov_row[1])
                salt = self._b64d(config['salt'])
                try:
                    unlock_kek_bytes = crypto.derive_kek_argon2id(
                        passphrase, salt, 32, config['iterations'], config['memory_kib'], config['parallelism']
                    )

                    wrap_aad = aad_policy.build_aad_bytes(
                        aad_policy_name,
                        wrapped_kid=db_kid,
                        wrapping_kid=wrapping_kid
                    )

                    db_kek_bytes = crypto.decrypt_aead(unlock_kek_bytes, nonce, wrapped_key, wrap_aad)
                    self.active_db_kek = db_kek_bytes
                    self.active_db_kid = db_kid
                    unwrapped = True
                    break
                except Exception as e:
                    # In a real implementation we might want to log or be more specific
                    # based on cryptography's InvalidTag exceptions
                    continue

        if not unwrapped:
            self.lock()
            raise errors.UnlockFailed("Failed to unlock database")

    def store_payload(self, schema_uuid: str, content_type: str, payload: dict) -> str:
        """Encrypts and stores a JSON payload."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")
        if not self.active_db_kek:
            raise errors.StorageLocked("Database is locked")

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
            wrap_id = self._generate_kid()
            cur.execute(
                "INSERT INTO wrapped_key_tbl (wrap_id, wrapped_kid, wrapping_kid, envelope_v, envelope_type, wrap_alg, nonce, wrapped_key, aad_policy, created_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (wrap_id, record_kid, self.active_db_kid, 1, 'key_wrap', alg, nonce_wrap, wrapped_record_dek, wrap_aad_policy, self._current_ms())
            )
            cur.execute(
                "INSERT INTO encrypted_object_tbl (object_uuid, envelope_v, envelope_type, schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy, created_at_ms, updated_at_ms) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (object_uuid, 1, 'aead', schema_uuid, content_type, alg, record_kid, nonce_payload, ciphertext, payload_aad_policy, self._current_ms(), self._current_ms())
            )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise errors.DatabaseBackendError(f"Database error during store: {e}") from e
        except Exception as e:
            self.conn.rollback()
            raise e

        return object_uuid

    def retrieve_payload(self, object_uuid: str) -> dict:
        """Retrieves and decrypts a payload."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")
        if not self.active_db_kek:
            raise errors.StorageLocked("Database is locked")

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT schema_uuid, content_type, alg, kid, nonce, ciphertext, aad_policy FROM encrypted_object_tbl WHERE object_uuid = ?", (object_uuid,))
            row = cur.fetchone()
        except sqlite3.Error as e:
            raise errors.DatabaseBackendError(f"Database error during retrieve: {e}") from e

        if not row:
            raise errors.ObjectNotFound("Object not found")

        schema_uuid, content_type, alg, record_kid, nonce_payload, ciphertext, payload_aad_policy = row
        aad_policy.get_policy(payload_aad_policy)

        # Get wrapped record DEK
        try:
            cur.execute("SELECT nonce, wrapped_key, aad_policy FROM wrapped_key_tbl WHERE wrapped_kid = ? AND wrapping_kid = ?", (record_kid, self.active_db_kid))
            wrap_row = cur.fetchone()
        except sqlite3.Error as e:
            raise errors.DatabaseBackendError(f"Database error during record key retrieval: {e}") from e

        if not wrap_row:
            raise errors.IntegrityCheckFailed("Record DEK wrap info not found")

        nonce_wrap, wrapped_record_dek, wrap_aad_policy = wrap_row
        aad_policy.get_policy(wrap_aad_policy)

        wrap_aad_bytes = aad_policy.build_aad_bytes(
            wrap_aad_policy,
            wrapped_kid=record_kid,
            wrapping_kid=self.active_db_kid
        )

        # Unwrap record DEK
        record_dek_bytes = crypto.decrypt_aead(self.active_db_kek, nonce_wrap, wrapped_record_dek, wrap_aad_bytes)

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


    def is_closed(self) -> bool:
        return self._is_closed

    def is_unlocked(self) -> bool:
        if self._is_closed:
            return False
        return self.active_db_kek is not None

    def get_status(self) -> str:
        if self._is_closed:
            return "closed"
        if self.active_db_kek is not None:
            return "open_unlocked"
        if not self.conn:
            return "closed"
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' AND status = 'active' LIMIT 1")
            res = cur.fetchone()
            if not res:
                return "uninitialized"
        except sqlite3.OperationalError:
            return "uninitialized"
        except sqlite3.ProgrammingError:
            return "closed"
        return "open_locked"

    def lock(self):
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")
        if self.active_db_kek is not None:
            self.active_db_kek = None
        self.active_db_kid = None

    def close(self):
        if self._is_closed:
            return
        if self.conn:
            self.conn.close()
            self.conn = None
        self.active_db_kek = None
        self.active_db_kid = None
        self._is_closed = True
