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
        from encrypted_storage import __version__ as package_version
        assert meta["created_by_version"] == package_version
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
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = '2' WHERE property = 'format_major'")
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

@pytest.mark.parametrize("property_name", [
    "storage_format_id",
    "format_major",
    "format_minor",
    "schema_version",
    "database_uuid",
    "created_at_ms",
    "created_by_library",
    "created_by_version",
    "sqlite_application_id",
    "sqlite_user_version",
    "required_features",
    "optional_features",
])
def test_missing_metadata_property(tmp_path, property_name):
    db_path = str(tmp_path / f"test_{property_name}.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("DELETE FROM storage_metadata_tbl WHERE property = ?", (property_name,))
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

@pytest.mark.parametrize("invalid_val", [
    "", "-1", "+1", "1.0", "1e3", " 123", "123 ", "abc", "001", "00"
])
def test_invalid_created_at_ms(tmp_path, invalid_val):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_at_ms'", (invalid_val,))
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

@pytest.mark.parametrize("invalid_val", [
    "", "   ", "\t\n"
])
def test_invalid_created_by(tmp_path, invalid_val):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_by_library'", (invalid_val,))
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

    db_path = str(tmp_path / "test2.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'created_by_version'", (invalid_val,))
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

def test_provenance_not_gate(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = 'some-other-implementation' WHERE property = 'created_by_library'")
        cur.execute("UPDATE storage_metadata_tbl SET value = '9.9.9-test' WHERE property = 'created_by_version'")
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        storage2.unlock_database("password")
        assert storage2.is_unlocked()
    finally:
        storage2.close()

def test_legacy_version_diagnostic_metadata(tmp_path):
    db_path = str(tmp_path / "test.sqlite")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = '0.0.0-dev' WHERE property = 'created_by_version'")
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        storage2.unlock_database("password")
        assert storage2.is_unlocked()
    finally:
        storage2.close()

@pytest.mark.parametrize("invalid_val", [
    "{}", '""', '"[]"', "null", "123", "0", "true", "false", "[1]", "[\"unknown_feature\"]", "[ ]", "[\n]", "[ \n\t]", "invalid"
])
def test_invalid_feature_flags(tmp_path, invalid_val):
    db_path = str(tmp_path / "test_req.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'required_features'", (invalid_val,))
        conn.commit()

    storage2 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

    db_path2 = str(tmp_path / "test_opt.db")
    storage_opt = EncryptedStorage(db_path2)
    storage_opt.initialize_database("password", "linux")
    storage_opt.close()

    with sqlite3.connect(db_path2) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'optional_features'", (invalid_val,))
        conn.commit()

    storage_opt2 = EncryptedStorage(db_path2)
    with pytest.raises(InvalidStorageFormat):
        storage_opt2.unlock_database("password")
    storage_opt2.close()

def test_database_uuid_format(tmp_path):
    invalid_uuids = [
        "AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA",
        "malformed-uuid",
        "12345678123442348234123456789012",
    ]
    for i, invalid_uuid in enumerate(invalid_uuids):
        db_path = str(tmp_path / f"test_uuid_{i}.db")
        storage = EncryptedStorage(db_path)
        storage.initialize_database("password", "linux")
        storage.close()

        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE storage_metadata_tbl SET value = ? WHERE property = 'database_uuid'", (invalid_uuid,))
            conn.commit()

        storage2 = EncryptedStorage(db_path)
        try:
            with pytest.raises(InvalidStorageFormat):
                storage2.unlock_database("password")
        finally:
            storage2.close()

def test_invalid_versions(tmp_path):
    cases = [
        ("format_major", "2"),
        ("format_minor", "1"),
        ("schema_version", "2")
    ]
    for prop, val in cases:
        db_path = str(tmp_path / f"test_{prop}.db")
        storage = EncryptedStorage(db_path)
        storage.initialize_database("password", "linux")
        storage.close()

        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("UPDATE storage_metadata_tbl SET value = ? WHERE property = ?", (val, prop))
            conn.commit()

        storage2 = EncryptedStorage(db_path)
        try:
            with pytest.raises(InvalidStorageFormat):
                storage2.unlock_database("password")
        finally:
            storage2.close()

def test_invalid_provider_config_combinations(tmp_path):
    modifiers = [
        lambda c: {k: v for k, v in c.items() if k != "profile"},
        lambda c: {**c, "profile": "argon2id-profile-v2"},
        lambda c: {**c, "kdf": "pbkdf2"},
        lambda c: {**c, "memory_kib": 1024},
        lambda c: {**c, "iterations": 4},
        lambda c: {**c, "parallelism": 2},
        lambda c: {**c, "output_bytes": 16},
        lambda c: {k: v for k, v in c.items() if k != "salt"},
        lambda c: {**c, "salt": c["salt"] + "="},
        lambda c: {**c, "salt": "invalid+salt/char"},
        lambda c: {**c, "salt": "MTIzNDU2Nzg5MDEyMzQ1"},
        lambda c: '{ "profile": "argon2id-profile-v1", "kdf": "argon2id" }'
    ]

    import jcs

    for i, mod in enumerate(modifiers):
        db_path = str(tmp_path / f"test_config_{i}.db")
        storage = EncryptedStorage(db_path)
        storage.initialize_database("password", "linux")
        storage.close()

        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT kid, provider_config_json FROM unlock_kek_tbl WHERE unlock_provider = 'passphrase_argon2id'")
            row = cur.fetchone()
            kid = row[0]
            config = json.loads(row[1])

            new_config = mod(config)
            if isinstance(new_config, str):
                canonical_config = new_config
            else:
                canonical_config = jcs.canonicalize(new_config).decode("utf-8")

            cur.execute("UPDATE unlock_kek_tbl SET provider_config_json = ? WHERE kid = ?", (canonical_config, kid))
            conn.commit()

        storage2 = EncryptedStorage(db_path)
        try:
            with pytest.raises(InvalidStorageFormat):
                storage2.unlock_database("password")
        finally:
            storage2.close()

def test_malformed_provider_config_json(tmp_path):
    db_path = str(tmp_path / "test_malformed_json.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA ignore_check_constraints = ON")
        cur = conn.cursor()
        cur.execute("UPDATE unlock_kek_tbl SET provider_config_json = '{ malformed' WHERE unlock_provider = 'passphrase_argon2id'")
        conn.commit()
        conn.execute("PRAGMA ignore_check_constraints = OFF")

    storage2 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

def test_pragma_validation(tmp_path):
    db_path = str(tmp_path / "test.db")
    storage = EncryptedStorage(db_path)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA application_id")
        assert cur.fetchone()[0] == 1447906135
        cur.execute("PRAGMA user_version")
        assert cur.fetchone()[0] == 1

    db_path2 = str(tmp_path / "test_app_id.db")
    storage = EncryptedStorage(db_path2)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path2) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA application_id = 0")
        conn.commit()

    storage2 = EncryptedStorage(db_path2)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage2.unlock_database("password")
    finally:
        storage2.close()

    db_path3 = str(tmp_path / "test_user_version.db")
    storage = EncryptedStorage(db_path3)
    storage.initialize_database("password", "linux")
    storage.close()

    with sqlite3.connect(db_path3) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA user_version = 2")
        conn.commit()

    storage3 = EncryptedStorage(db_path3)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage3.unlock_database("password")
    finally:
        storage3.close()


def test_error_precedence(tmp_path):
    import uuid
    db_path = str(tmp_path / f"test_{uuid.uuid4().hex}.db")
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

    # 4. Storage format metadata failure -> InvalidStorageFormat
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("UPDATE storage_metadata_tbl SET value = 'invalid' WHERE property = 'format_major'")
        conn.commit()

    storage3 = EncryptedStorage(db_path)
    try:
        with pytest.raises(InvalidStorageFormat):
            storage3.unlock_database("password")
    finally:
        storage3.close()
