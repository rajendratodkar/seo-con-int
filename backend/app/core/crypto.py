"""Local at-rest encryption for API keys.

The key material lives in data/runtime/secret.key (gitignored). This protects
stored keys from casual inspection; it is NOT a substitute for OS-level secret
storage, which the Tauri shell can add later.
"""
from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings

_KEY_FILE_NAME = "secret.key"


def _load_fernet() -> Fernet:
    runtime_dir = settings.data_dir / "runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    key_file = runtime_dir / _KEY_FILE_NAME
    if not key_file.exists():
        key_file.write_bytes(Fernet.generate_key())
    return Fernet(key_file.read_bytes())


def encrypt_secret(plain: str) -> str:
    return _load_fernet().encrypt(plain.encode("utf-8")).decode("ascii")


def decrypt_secret(token: str) -> str | None:
    try:
        return _load_fernet().decrypt(token.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError):
        return None
