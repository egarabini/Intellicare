"""
Secrets Manager for IntelliCare Bots.
Encrypts and decrypts secret values using symmetric encryption (Fernet).
"""
import os
from cryptography.fernet import Fernet
from typing import Dict, Optional
from sqlalchemy.orm import Session
from intellicare_core.bots.models import BotSecret

# Use a permanent key from the environment, fallback to a deterministic local one for dev.
# In production, INTELLICARE_BOT_ENCRYPTION_KEY MUST be set and backed up.
_ENCRYPTION_KEY = os.getenv(
    "INTELLICARE_BOT_ENCRYPTION_KEY", 
    "A-secure-base64-random-key-override-in-prod="
)

# Ensure the key is exactly 32 url-safe base64-encoded bytes.
# For local dev fallback, we pad or derive a valid Fernet key.
try:
    _fernet = Fernet(_ENCRYPTION_KEY.encode('utf-8'))
except ValueError:
    import base64
    import hashlib
    # Derive a valid 32-byte fernet key from the invalid string
    _derived = hashlib.sha256(_ENCRYPTION_KEY.encode('utf-8')).digest()
    _fernet = Fernet(base64.urlsafe_b64encode(_derived))

def encrypt_secret(value: str) -> str:
    """Encrypts a plaintext string into a Fernet token."""
    return _fernet.encrypt(value.encode('utf-8')).decode('utf-8')

def decrypt_secret(encrypted_value: str) -> str:
    """Decrypts a Fernet token back into plaintext string."""
    return _fernet.decrypt(encrypted_value.encode('utf-8')).decode('utf-8')

def get_tenant_bot_secrets(session: Session, tenant_id: str, bot_id: Optional[str] = None) -> Dict[str, str]:
    """
    Retrieves all decrypted secrets available for a specific bot in a tenant.
    Includes both tenant-global secrets (bot_id=None) and bot-specific secrets.
    """
    query = session.query(BotSecret).filter(BotSecret.tenant_id == tenant_id)
    
    if bot_id:
        query = query.filter((BotSecret.bot_id == bot_id) | (BotSecret.bot_id.is_(None)))
    else:
        query = query.filter(BotSecret.bot_id.is_(None))
        
    secrets = query.all()
    
    # Decrypt and build the dictionary (bot-specific overrides global ones with the same name)
    # Start with globals, then override with bot specific
    unlocked = {}
    for secret in sorted(secrets, key=lambda s: s.bot_id is not None):
        try:
            unlocked[secret.name] = decrypt_secret(secret.value_encrypted)
        except Exception:
            # If decryption fails (e.g. key rotated/lost), the secret is inaccessible 
            # rather than crashing the bot completely.
            unlocked[secret.name] = "<decryption-failed>"
            
    return unlocked
