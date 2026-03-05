import uuid
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# --- Bot Schemas ---

class BotBase(BaseModel):
    name: str
    description: Optional[str] = None
    code: str
    runtime: str = "sandbox"
    status: str = "active"
    run_as_user: bool = False
    timeout_seconds: int = 30

class BotCreate(BotBase):
    pass

class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    code: Optional[str] = None
    runtime: Optional[str] = None
    status: Optional[str] = None
    run_as_user: Optional[bool] = None
    timeout_seconds: Optional[int] = None

class BotResponse(BotBase):
    id: uuid.UUID
    tenant_id: str
    code_version: int
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# --- Bot Secret Schemas ---

class BotSecretCreate(BaseModel):
    name: str
    value: str # Plaintext value to be encrypted
    bot_id: Optional[uuid.UUID] = None # If None, it's a global tenant secret

class BotSecretResponse(BaseModel):
    id: uuid.UUID
    tenant_id: str
    bot_id: Optional[uuid.UUID] = None
    name: str
    # NEVER expose value_encrypted or decrypted values in the generic response

    class Config:
        from_attributes = True

# --- Bot Execution Schemas ---

class BotExecutionResponse(BaseModel):
    id: uuid.UUID
    bot_id: uuid.UUID
    tenant_id: str
    subscription_id: Optional[uuid.UUID] = None
    input_resource_type: Optional[str] = None
    input_resource_id: Optional[str] = None
    interaction: Optional[str] = None
    success: bool
    log_output: Optional[str] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
