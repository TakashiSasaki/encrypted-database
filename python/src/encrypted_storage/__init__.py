from .storage import EncryptedStorage
from .errors import *
import importlib.metadata
import re
import os

try:
    __version__ = importlib.metadata.version("encrypted_storage")
except importlib.metadata.PackageNotFoundError:
    # Fallback to reading pyproject.toml if installed in editable mode without metadata
    __version__ = "0.0.0-dev"
    try:
        pyproject_path = os.path.join(os.path.dirname(__file__), "..", "..", "pyproject.toml")
        if os.path.exists(pyproject_path):
            with open(pyproject_path, "r", encoding="utf-8") as f:
                content = f.read()
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    __version__ = match.group(1)
    except Exception:
        pass

__all__ = [
    "EncryptedStorage",
    "StorageError",
    "StorageClosed",
    "StorageLocked",
    "StorageNotInitialized",
    "StorageAlreadyInitialized",
    "InvalidStorageFormat",
    "UnlockFailed",
    "ObjectNotFound",
    "UnsupportedPlatform",
    "InvalidUuid",
    "InvalidContentType",
    "InvalidPayload",
    "IntegrityCheckFailed",
    "CryptoOperationFailed",
    "DatabaseBackendError",
    "AadPolicyError",
    "InvalidPassphrase",
]
