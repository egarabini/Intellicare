"""Funções de criptografia para dados sensíveis em repouso (Fernet / AES-128-CBC)."""
from __future__ import annotations

from cryptography.fernet import Fernet

from intellicare_core.config.settings import get_settings


def _fernet() -> Fernet:
    key = get_settings().server_encryption_key
    if not key or key == "CHANGE_ME_GENERATE_WITH_FERNET":
        raise RuntimeError(
            "SERVER_ENCRYPTION_KEY não configurada. "
            "Gere com: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_bytes(data: bytes) -> bytes:
    return _fernet().encrypt(data)


def decrypt_bytes(token: bytes) -> bytes:
    return _fernet().decrypt(token)


def encrypt_text(text: str) -> str:
    return _fernet().encrypt(text.encode()).decode()


def decrypt_text(token: str) -> str:
    return _fernet().decrypt(token.encode()).decode()
