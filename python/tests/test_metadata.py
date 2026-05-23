import pytest
import sqlite3
import json
import base64
from encrypted_storage.storage import EncryptedStorage
from encrypted_storage.errors import InvalidStorageFormat, StorageClosed, InvalidPassphrase, UnlockFailed, StorageNotInitialized

def test_metadata_properties(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")

    # Verify metadata created
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT property, value FROM storage_metadata_tbl")
        meta = {row[0]: row[1] for row in cur.fetchall()}

        assert meta["storage_format_id"] == "vault.moukaeritai.work.storage"
        assert meta["format_major"] == "1"
        assert meta["format_minor"] == "0"
        assert meta["schema_version"] == "1"
        assert meta["created_by_library"] == "python"
        assert meta["created_by_version"] == "0.0.0-dev"
        assert meta["sqlite_application_id"] == "1447906135"
        assert meta["sqlite_user_version"] == "1"
        assert "database_uuid" in meta
        assert meta["created_at_ms"].isdigit()
        assert meta["required_features"] == "[]"
        assert meta["optional_features"] == "[]"

        # Pragma checks
        cur.execute("PRAGMA application_id")
        assert cur.fetchone()[0] == 1447906135
        cur.execute("PRAGMA user_version")
        assert cur.fetchone()[0] == 1

        storage.close()

def test_invalid_metadata(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = '2' WHERE property = 'format_major'")
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    with pytest.raises(InvalidStorageFormat):
        storage2.unlock_database("password")

def test_missing_metadata_property(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM storage_metadata_tbl WHERE property = 'database_uuid'")
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    with pytest.raises(InvalidStorageFormat):
        storage2.unlock_database("password")

def test_invalid_feature(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = '[\"unknown_feature\"]' WHERE property = 'required_features'")
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    with pytest.raises(InvalidStorageFormat):
        storage2.unlock_database("password")

def test_invalid_jcs_feature(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = '[ ]' WHERE property = 'required_features'")
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    with pytest.raises(InvalidStorageFormat):
        storage2.unlock_database("password")

def test_invalid_provider_config(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        # Change KDF to something else
        cur.execute("SELECT kid, provider_config_json FROM unlock_kek_tbl WHERE unlock_provider = 'passphrase_argon2id'")
        row = cur.fetchone()
        kid = row[0]
        config = json.loads(row[1])
        config["kdf"] = "pbkdf2"

        import jcs
        canonical_config = jcs.canonicalize(config).decode("utf-8")

        cur.execute("UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?", (canonical_config, kid))
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    with pytest.raises(InvalidStorageFormat):
        storage2.unlock_database("password")

def test_error_precedence(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    # 1. Closed storage + invalid arg -> StorageClosed
    with pytest.raises(StorageClosed):
        storage.unlock_database(123)

    storage2 = EncryptedStorage(db_path)
    # 2. Open storage + invalid arg -> InvalidPassphrase
    with pytest.raises(InvalidPassphrase):
        storage2.unlock_database(123)

    # 3. Open storage + wrong arg -> UnlockFailed
    with pytest.raises(UnlockFailed):
        storage2.unlock_database("wrong")
