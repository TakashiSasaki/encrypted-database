import math
import sqlite3
import time
import uuid
import json
import base64
import re
from pathlib import Path

from . import aad_policy, crypto, errors

class EncryptedStorage:
    _UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$')

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        is_empty_db = self.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' LIMIT 1").fetchone() is None
        if is_empty_db:
            self.conn.execute("PRAGMA page_size = 4096")
            self.conn.execute("PRAGMA auto_vacuum = NONE")
        try:
            self.conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.Error as e:
            import logging
            logging.getLogger(__name__).debug(f"Failed to enable WAL mode: {e}")
        try:
            self.conn.execute("PRAGMA synchronous = NORMAL")
        except sqlite3.Error:
            pass
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.active_db_kek = None
        self.active_db_kid = None
        self._is_closed = False

    def _bootstrap_schema(self):
        schema_path = Path(__file__).parent.parent.parent.parent / "docs" / "backend" / "sqlite" / "schema.sql"
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        self.conn.executescript(schema_sql)
        self.conn.execute("PRAGMA application_id = 1447906135")
        self.conn.execute("PRAGMA user_version = 1")
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

    def _validate_uuid(self, value: str, field_name: str):
        if not isinstance(value, str) or not self._UUID_PATTERN.match(value):
            raise errors.InvalidUuid(f"Invalid {field_name}: must be a canonical lowercase hyphenated UUID")

    def _validate_content_type(self, value: str):
        if not isinstance(value, str) or not value.strip():
            raise errors.InvalidContentType("Content type must be a non-empty string")
        if any(ord(c) < 32 or ord(c) == 127 for c in value):
            raise errors.InvalidContentType("Content type must not contain control characters")
        if '/' not in value:
            raise errors.InvalidContentType("Content type must be a basic type/subtype format")

    def _validate_payload(self, value: object, path: str = "$", is_top_level: bool = True, visited: set = None):
        if visited is None:
            visited = set()

        if id(value) in visited:
            raise errors.InvalidPayload(f"Invalid payload at {path}: cyclic reference detected")

        if type(value) in (dict, list):
            visited.add(id(value))

        if is_top_level:
            if type(value) is not dict:
                raise errors.InvalidPayload(f"Invalid payload at {path}: must be a dictionary/JSON object at top level")

        if type(value) is dict:
            for k, v in value.items():
                if type(k) is not str:
                    raise errors.InvalidPayload(f"Invalid payload at {path}: dictionary keys must be strings")
                self._validate_payload(v, path=f"{path}.{k}", is_top_level=False, visited=visited)
        elif type(value) is list:
            for i, v in enumerate(value):
                self._validate_payload(v, path=f"{path}[{i}]", is_top_level=False, visited=visited)
        elif type(value) is bool:
            pass
        elif type(value) is int:
            pass
        elif type(value) is float:
            if math.isnan(value) or math.isinf(value):
                raise errors.InvalidPayload(f"Invalid payload at {path}: NaN and Infinity are not valid JSON")
        elif type(value) is str:
            pass
        elif value is None:
            pass
        else:
            raise errors.InvalidPayload(f"Invalid payload at {path}: unsupported type {type(value).__name__}")

        if type(value) in (dict, list):
            visited.remove(id(value))

    def initialize_database(self, passphrase: str, platform: str):
        """Initializes a new database with a new database_kek wrapped by a new unlock_kek."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")

        if not isinstance(passphrase, str):
            raise errors.InvalidPassphrase("Passphrase must be a string")
        if not isinstance(platform, str):
            raise errors.UnsupportedPlatform("Platform must be a string")
        if self.is_unlocked():
            raise errors.StorageAlreadyInitialized("Storage is already initialized")
        try:
            cur = self.conn.cursor()
            cur.execute("SELECT kid FROM key_tbl WHERE key_class = 'database_kek' LIMIT 1")
            if cur.fetchone():
                raise errors.StorageAlreadyInitialized("Storage is already initialized")
        except sqlite3.OperationalError:
            pass
        cur = self.conn.cursor()
        cur.execute("SELECT 1 FROM sqlite_master WHERE type='table'")
        if not cur.fetchone():
            self._bootstrap_schema()
        else:
            cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='storage_metadata_tbl'")
            if not cur.fetchone():
                raise errors.InvalidStorageFormat("Cannot initialize non-empty pre-v1 database")
            cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='key_tbl'")
            if not cur.fetchone():
                raise errors.InvalidStorageFormat("Cannot initialize unsupported database format")

        self._validate_platform(platform)

        db_kek_bytes = crypto.generate_random_bytes(32)
        db_kid = self._generate_kid()

        # Derive unlock KEK
        salt = crypto.generate_random_bytes(crypto.ARGON2ID_PROFILE_V1_SALT_BYTES)
        time_cost = crypto.ARGON2ID_PROFILE_V1_ITERATIONS
        memory_cost = crypto.ARGON2ID_PROFILE_V1_MEMORY_KIB
        parallelism = crypto.ARGON2ID_PROFILE_V1_PARALLELISM
        output_bytes = crypto.ARGON2ID_PROFILE_V1_OUTPUT_BYTES

        unlock_kek_bytes = crypto.derive_kek_argon2id(passphrase, salt, output_bytes, time_cost, memory_cost, parallelism)
        unlock_kid = self._generate_kid()

        provider_config = {
            "kdf": "argon2id",
            "profile": "argon2id-profile-v1",
            "salt": self._b64e(salt),
            "memory_kib": memory_cost,
            "iterations": time_cost,
            "parallelism": parallelism,
            "output_bytes": output_bytes
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
            db_uuid = str(uuid.uuid4())
            from . import __version__ as package_version

            metadata = {
                "storage_format_id": "vault.moukaeritai.work.storage",
                "format_major": "1",
                "format_minor": "0",
                "schema_version": "1",
                "database_uuid": db_uuid,
                "created_at_ms": str(self._current_ms()),
                "created_by_library": "python",
                "created_by_version": package_version,
                "sqlite_application_id": "1447906135",
                "sqlite_user_version": "1",
                "required_features": crypto.canonicalize_json([]).decode("utf-8"),
                "optional_features": crypto.canonicalize_json([]).decode("utf-8")
            }
            for prop, val in metadata.items():
                cur.execute("INSERT INTO storage_metadata_tbl (property, value) VALUES (?, ?)", (prop, val))

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

        if not isinstance(passphrase, str):
            raise errors.InvalidPassphrase("Passphrase must be a string")

        if not self.conn:
            raise errors.StorageNotInitialized("Database not initialized")
        cur = self.conn.cursor()

        self._validate_v1_metadata()

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
                prov_config_str = prov_row[1]
                try:
                    config = json.loads(prov_config_str)
                    import jcs
                    canonical_config = jcs.canonicalize(config).decode("utf-8")
                    if canonical_config != prov_config_str:
                        raise errors.InvalidStorageFormat("provider_config_json is not valid JCS canonical JSON")
                except Exception as e:
                    if isinstance(e, errors.InvalidStorageFormat):
                        raise e
                    raise errors.InvalidStorageFormat("provider_config_json is not valid JSON")

                required_config_props = ["kdf", "profile", "salt", "memory_kib", "iterations", "parallelism", "output_bytes"]
                for prop in required_config_props:
                    if prop not in config:
                        raise errors.InvalidStorageFormat(f"Missing provider_config_json property: {prop}")

                if config["profile"] != "argon2id-profile-v1":
                    raise errors.InvalidStorageFormat("Unknown or missing profile in provider_config_json")

                if config["kdf"] != "argon2id" or config["memory_kib"] != 65536 or \
                   config["iterations"] != 3 or config["parallelism"] != 1 or \
                   config["output_bytes"] != 32:
                    raise errors.InvalidStorageFormat("provider_config_json explicit parameters mismatch argon2id-profile-v1")

                salt_str = config['salt']
                if '=' in salt_str or not re.match(r'^[A-Za-z0-9_-]+$', salt_str):
                    raise errors.InvalidStorageFormat("salt must be base64url encoded with no padding")

                try:
                    salt = self._b64d(salt_str)
                except Exception:
                    raise errors.InvalidStorageFormat("salt is not valid base64url")

                if len(salt) != 16:
                    raise errors.InvalidStorageFormat("decoded salt length is not 16 bytes")

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

        self._validate_uuid(schema_uuid, "schema_uuid")
        self._validate_content_type(content_type)
        self._validate_payload(payload)

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

    def update_payload(self, object_uuid: str, schema_uuid: str, content_type: str, payload: dict) -> None:
        """Updates an existing JSON payload and its metadata."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")

        self._validate_uuid(object_uuid, "object_uuid")
        self._validate_uuid(schema_uuid, "schema_uuid")
        self._validate_content_type(content_type)
        self._validate_payload(payload)

        if not self.active_db_kek:
            raise errors.StorageLocked("Database is locked")

        cur = self.conn.cursor()
        try:
            cur.execute("SELECT kid, alg, created_at_ms FROM encrypted_object_tbl WHERE object_uuid = ?", (object_uuid,))
            row = cur.fetchone()
        except sqlite3.Error as e:
            raise errors.DatabaseBackendError(f"Database error during update lookup: {e}") from e

        if not row:
            raise errors.ObjectNotFound("Object not found")

        record_kid, alg, created_at_ms = row

        if alg != "A256GCM":
            raise errors.InvalidStorageFormat("Unsupported object alg")

        try:
            cur.execute("SELECT status FROM key_tbl WHERE kid = ? AND key_class = 'record_dek'", (record_kid,))
            key_row = cur.fetchone()
        except sqlite3.Error as e:
            raise errors.DatabaseBackendError(f"Database error during record DEK lookup: {e}") from e

        if not key_row:
            raise errors.ObjectNotFound("Record DEK not found")

        if key_row[0] != "active":
            raise errors.InvalidStorageFormat("Record DEK is not active")

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

        record_dek_bytes = crypto.decrypt_aead(self.active_db_kek, nonce_wrap, wrapped_record_dek, wrap_aad_bytes)

        # Encrypt updated payload with existing record DEK
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

        cur.execute("BEGIN TRANSACTION")
        try:
            cur.execute(
                "UPDATE encrypted_object_tbl SET schema_uuid = ?, content_type = ?, nonce = ?, ciphertext = ?, aad_policy = ?, updated_at_ms = ? WHERE object_uuid = ?",
                (schema_uuid, content_type, nonce_payload, ciphertext, payload_aad_policy, self._current_ms(), object_uuid)
            )
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise errors.DatabaseBackendError(f"Database error during update: {e}") from e
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_payload(self, object_uuid: str) -> None:
        """Deletes a payload."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")

        self._validate_uuid(object_uuid, "object_uuid")

        if not self.active_db_kek:
            raise errors.StorageLocked("Database is locked")

        cur = self.conn.cursor()
        cur.execute("BEGIN TRANSACTION")
        try:
            cur.execute("DELETE FROM encrypted_object_tbl WHERE object_uuid = ?", (object_uuid,))
            if cur.rowcount == 0:
                self.conn.rollback()
                raise errors.ObjectNotFound("Object not found")
            self.conn.commit()
        except sqlite3.Error as e:
            self.conn.rollback()
            raise errors.DatabaseBackendError(f"Database error during delete: {e}") from e
        except Exception as e:
            self.conn.rollback()
            raise e

    def retrieve_payload(self, object_uuid: str) -> dict:
        """Retrieves and decrypts a payload."""
        if self._is_closed:
            raise errors.StorageClosed("Storage is closed")

        self._validate_uuid(object_uuid, "object_uuid")

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

    def _validate_v1_metadata(self):
        cur = self.conn.cursor()

        # Check if metadata table exists
        try:
            cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='storage_metadata_tbl'")
            if not cur.fetchone():
                raise errors.InvalidStorageFormat("No storage_metadata_tbl found (pre-v1 DB)")
        except sqlite3.Error as e:
            raise errors.DatabaseBackendError(f"Database error during metadata check: {e}") from e

        # Validate PRAGMA application_id and user_version
        try:
            cur.execute("PRAGMA application_id")
            app_id = cur.fetchone()[0]
            if str(app_id) != "1447906135":
                raise errors.InvalidStorageFormat(f"Invalid PRAGMA application_id: {app_id}")

            cur.execute("PRAGMA user_version")
            user_version = cur.fetchone()[0]
        except sqlite3.Error as e:
            raise errors.DatabaseBackendError(f"Database error during PRAGMA check: {e}") from e

        # Validate storage_metadata_tbl
        try:
            cur.execute("SELECT property, value FROM storage_metadata_tbl")
            metadata_rows = cur.fetchall()
            if not metadata_rows:
                raise errors.InvalidStorageFormat("storage_metadata_tbl is empty (invalid V1 DB)")
            metadata = {k: v for k, v in metadata_rows}
        except sqlite3.Error as e:
            if "no such table" in str(e):
                raise errors.InvalidStorageFormat("No storage_metadata_tbl found (pre-v1 DB)")
            raise errors.DatabaseBackendError(f"Database error during metadata read: {e}") from e

        required_props = [
            "storage_format_id", "format_major", "format_minor", "schema_version",
            "database_uuid", "created_at_ms", "created_by_library", "created_by_version",
            "sqlite_application_id", "sqlite_user_version",
            "required_features", "optional_features"
        ]
        for prop in required_props:
            if prop not in metadata:
                raise errors.InvalidStorageFormat(f"Missing metadata property: {prop}")

        if metadata["storage_format_id"] != "vault.moukaeritai.work.storage":
            raise errors.InvalidStorageFormat("Invalid storage_format_id")
        if metadata["format_major"] != "1":
            raise errors.InvalidStorageFormat("Invalid format_major")
        if metadata["format_minor"] != "0":
            raise errors.InvalidStorageFormat("Invalid format_minor")
        if metadata["schema_version"] != "1":
            raise errors.InvalidStorageFormat("Invalid schema_version")
        if metadata["sqlite_application_id"] != "1447906135":
            raise errors.InvalidStorageFormat("Invalid metadata sqlite_application_id")
        if metadata["sqlite_user_version"] != "1":
            raise errors.InvalidStorageFormat("Invalid metadata sqlite_user_version")
        if str(user_version) != "1":
            raise errors.InvalidStorageFormat("PRAGMA user_version and metadata contradiction")

        if not self._UUID_PATTERN.match(metadata["database_uuid"]):
            raise errors.InvalidStorageFormat("Invalid canonical database_uuid")

        if not re.match(r'^(0|[1-9][0-9]*)$', metadata["created_at_ms"]):
            raise errors.InvalidStorageFormat("Invalid created_at_ms format")

        if not isinstance(metadata["created_by_library"], str) or not metadata["created_by_library"].strip():
            raise errors.InvalidStorageFormat("Invalid created_by_library")

        if not isinstance(metadata["created_by_version"], str) or not metadata["created_by_version"].strip():
            raise errors.InvalidStorageFormat("Invalid created_by_version")

        # JCS validation for features
        try:
            req_feat_str = metadata["required_features"]
            req_feat = json.loads(req_feat_str)
            import jcs
            canonical_req = jcs.canonicalize(req_feat).decode("utf-8")
            if canonical_req != req_feat_str:
                raise errors.InvalidStorageFormat("Features are not valid JCS canonical JSON arrays")
            if not isinstance(req_feat, list) or len(req_feat) > 0:
                raise errors.InvalidStorageFormat("Unknown required features found")

            opt_feat_str = metadata["optional_features"]
            opt_feat = json.loads(opt_feat_str)
            canonical_opt = jcs.canonicalize(opt_feat).decode("utf-8")
            if canonical_opt != opt_feat_str:
                raise errors.InvalidStorageFormat("Features are not valid JCS canonical JSON arrays")
            if not isinstance(opt_feat, list) or len(opt_feat) > 0:
                raise errors.InvalidStorageFormat("Unknown optional features found")
        except Exception as e:
            if isinstance(e, errors.InvalidStorageFormat):
                raise e
            raise errors.InvalidStorageFormat("Features are not valid JSON arrays")
