"""SecretsManager — Fernet encryption for bot secrets at-rest.

Primary:  cryptography.fernet.Fernet (if installed)
Fallback: base64 (dev/test only — NOT secure for production)

The encryption key is loaded from the BOTS_SECRET_KEY env var.
In production, this should be a 32-byte URL-safe base64 key generated
by ``Fernet.generate_key()``.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

_KEY_ENV = "BOTS_SECRET_KEY"


def _get_key() -> bytes:
    raw = os.getenv(_KEY_ENV, "")
    if not raw:
        # Generate a stable dev key from a fixed seed
        seed = b"intellicare-bots-dev-key-0000000"
        return base64.urlsafe_b64encode(seed)
    return raw.encode()


def encrypt(plaintext: str) -> str:
    """Encrypt *plaintext* and return a base64-encoded ciphertext string."""
    try:
        from cryptography.fernet import Fernet  # type: ignore[import]

        f = Fernet(_get_key())
        return f.encrypt(plaintext.encode()).decode()
    except ImportError:
        logger.warning(
            "cryptography package not installed — using base64 fallback (NOT SECURE)"
        )
        return base64.b64encode(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    """Decrypt a ciphertext produced by :func:`encrypt`."""
    try:
        from cryptography.fernet import Fernet  # type: ignore[import]

        f = Fernet(_get_key())
        return f.decrypt(ciphertext.encode()).decode()
    except ImportError:
        return base64.b64decode(ciphertext.encode()).decode()


class SecretsManager:
    """Encrypt and decrypt bot secrets."""

    def encrypt_secret(self, value: str) -> str:
        return encrypt(value)

    def decrypt_secret(self, ciphertext: str) -> str:
        return decrypt(ciphertext)

    def decrypt_all(self, secrets_map: dict[str, str]) -> dict[str, str]:
        """Decrypt a {name: ciphertext} map → {name: plaintext}."""
        return {name: self.decrypt_secret(ct) for name, ct in secrets_map.items()}
