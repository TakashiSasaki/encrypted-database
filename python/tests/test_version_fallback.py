import pytest
import importlib.metadata
import os
import sys

def test_version_fallback_mechanism(monkeypatch):
    # This test verifies the fallback logic in __init__.py when package metadata is missing.

    # Temporarily remove encrypted_storage from sys.modules to force a reload
    if 'encrypted_storage' in sys.modules:
        del sys.modules['encrypted_storage']

    # Mock importlib.metadata.version to always raise PackageNotFoundError
    def mock_version(package_name):
        raise importlib.metadata.PackageNotFoundError(package_name)

    monkeypatch.setattr(importlib.metadata, 'version', mock_version)

    # Now import it; this should trigger the fallback logic reading pyproject.toml
    import encrypted_storage

    # We expect it to successfully read 0.1.0 from pyproject.toml in the repo
    assert encrypted_storage.__version__ == "0.1.0"

def test_version_fallback_exception(monkeypatch):
    if 'encrypted_storage' in sys.modules:
        del sys.modules['encrypted_storage']

    def mock_version(package_name):
        raise importlib.metadata.PackageNotFoundError(package_name)

    def mock_exists(path):
        raise OSError("Simulated permission denied")

    monkeypatch.setattr(importlib.metadata, 'version', mock_version)
    monkeypatch.setattr(os.path, 'exists', mock_exists)

    import encrypted_storage
    assert encrypted_storage.__version__ == "0.0.0-dev"
