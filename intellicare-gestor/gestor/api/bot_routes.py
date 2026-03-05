import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from gestor.api.deps import get_db, get_current_user
from gestor.schemas.bot_schemas import (
    BotCreate, BotUpdate, BotResponse, 
    BotSecretCreate, BotSecretResponse,
    BotExecutionResponse
)
from gestor.schemas.user_schemas import TenantUserResponse

# These rely on the models created in intellicare_core.bots
from intellicare_core.bots.models import Bot, BotSecret, BotExecution
from intellicare_core.bots.secrets_manager import encrypt_secret

router = APIRouter()

# --- BOTS ---

@router.get("/bots", response_model=List[BotResponse])
def list_bots(
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List all bots for the current tenant."""
    return db.query(Bot).filter(Bot.tenant_id == current_user.tenant_id).offset(skip).limit(limit).all()

@router.post("/bots", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
def create_bot(
    bot_in: BotCreate,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user)
):
    """Create a new bot."""
    bot = Bot(
        **bot_in.model_dump(),
        tenant_id=current_user.tenant_id,
        created_by=str(current_user.id)
    )
    db.add(bot)
    db.commit()
    db.refresh(bot)
    return bot

@router.get("/bots/{bot_id}", response_model=BotResponse)
def get_bot(
    bot_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user)
):
    """Get a specific bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.tenant_id == current_user.tenant_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    return bot

@router.put("/bots/{bot_id}", response_model=BotResponse)
def update_bot(
    bot_id: uuid.UUID,
    bot_in: BotUpdate,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user)
):
    """Update a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.tenant_id == current_user.tenant_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")

    update_data = bot_in.model_dump(exclude_unset=True)
    if "code" in update_data and update_data["code"] != bot.code:
        bot.code_version += 1

    for field, value in update_data.items():
        setattr(bot, field, value)

    db.commit()
    db.refresh(bot)
    return bot

@router.delete("/bots/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bot(
    bot_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user)
):
    """Delete a bot."""
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.tenant_id == current_user.tenant_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    db.delete(bot)
    db.commit()

# --- SECRETS ---

@router.get("/secrets", response_model=List[BotSecretResponse])
def list_secrets(
    bot_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user)
):
    """List bot secrets (does not expose values)."""
    query = db.query(BotSecret).filter(BotSecret.tenant_id == current_user.tenant_id)
    if bot_id:
        query = query.filter((BotSecret.bot_id == bot_id) | (BotSecret.bot_id.is_(None)))
    return query.all()

@router.post("/secrets", response_model=BotSecretResponse, status_code=status.HTTP_201_CREATED)
def create_secret(
    secret_in: BotSecretCreate,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user)
):
    """Create or update a secret for a bot or globally for the tenant."""
    # Check if exists
    existing = db.query(BotSecret).filter(
        BotSecret.tenant_id == current_user.tenant_id,
        BotSecret.bot_id == secret_in.bot_id,
        BotSecret.name == secret_in.name
    ).first()

    encrypted_val = encrypt_secret(secret_in.value)

    if existing:
        existing.value_encrypted = encrypted_val
        db.commit()
        db.refresh(existing)
        return existing
    else:
        secret = BotSecret(
            tenant_id=current_user.tenant_id,
            bot_id=secret_in.bot_id,
            name=secret_in.name,
            value_encrypted=encrypted_val
        )
        db.add(secret)
        db.commit()
        db.refresh(secret)
        return secret

@router.delete("/secrets/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_secret(
    secret_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user)
):
    """Delete a secret."""
    secret = db.query(BotSecret).filter(
        BotSecret.id == secret_id, 
        BotSecret.tenant_id == current_user.tenant_id
    ).first()
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found")
    
    db.delete(secret)
    db.commit()

# --- EXECUTIONS ---

@router.get("/bots/{bot_id}/executions", response_model=List[BotExecutionResponse])
def list_bot_executions(
    bot_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: TenantUserResponse = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """List execution history logs for a specific bot."""
    # Ensure bot belongs to tenant
    bot = db.query(Bot).filter(Bot.id == bot_id, Bot.tenant_id == current_user.tenant_id).first()
    if not bot:
        raise HTTPException(status_code=404, detail="Bot not found")
    
    return db.query(BotExecution).filter(
        BotExecution.bot_id == bot_id,
        BotExecution.tenant_id == current_user.tenant_id
    ).order_by(BotExecution.created_at.desc()).offset(skip).limit(limit).all()
