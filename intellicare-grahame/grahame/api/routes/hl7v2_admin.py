"""Admin routes for HL7v2 API Key management.

Este módulo fornece endpoints REST para gerenciar API Keys e IP whitelist.

⚠️  IMPORTANTE: Estes endpoints devem ser protegidos por autenticação administrativa
em produção (ex: Keycloak, JWT, etc.).
"""

import logging
import inspect
from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from grahame.models.hl7v2_api_key import HL7v2APIKey
from grahame.api.schemas.hl7v2_api_key import (
    HL7v2APIKeyCreate,
    HL7v2APIKeyUpdate,
    HL7v2APIKeyResponse,
    HL7v2APIKeyListResponse,
    IPWhitelistAddRequest,
    IPWhitelistRemoveRequest,
    IPWhitelistResponse,
)
from grahame.api.dependencies.hl7v2_auth import get_db_session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/hl7v2/api-keys", tags=["HL7v2 Admin"])


async def _get_db_session_dependency(request: Request):
    """Resolve DB dependency dynamically to support test-time patching."""
    provider = get_db_session
    try:
        result = provider(request)
    except TypeError:
        result = provider()

    if inspect.isasyncgen(result):
        async for session in result:
            yield session
        return

    if inspect.isawaitable(result):
        yield await result
        return

    yield result


def _ensure_api_key_defaults(api_key: HL7v2APIKey) -> HL7v2APIKey:
    """Ensure response-required fields exist when using mocked DB sessions."""
    if api_key.id is None:
        api_key.id = 0
    if api_key.created_at is None:
        api_key.created_at = datetime.now(timezone.utc)
    if api_key.usage_count is None:
        api_key.usage_count = 0
    if api_key.rate_limit_per_minute is None:
        api_key.rate_limit_per_minute = 0
    return api_key


@router.post("", response_model=HL7v2APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: HL7v2APIKeyCreate,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Cria uma nova API Key.
    
    Args:
        data: Dados da API Key
        db: Sessão do banco de dados
    
    Returns:
        HL7v2APIKeyResponse: API Key criada (incluindo a key gerada)
    
    ⚠️  IMPORTANTE: A API Key só é retornada nesta resposta. Salve-a com segurança!
    """
    # Gerar API Key
    api_key = HL7v2APIKey.generate_api_key()
    
    # Calcular expiração
    expires_at = None
    if data.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=data.expires_days)
    
    # Criar objeto
    api_key_obj = HL7v2APIKey(
        api_key=api_key,
        system_name=data.system_name,
        system_identifier=data.system_identifier,
        description=data.description,
        is_active=True,
        expires_at=expires_at,
        rate_limit_per_minute=data.rate_limit_per_minute,
        allowed_ips=data.allowed_ips,
        created_by="admin",  # TODO: Get from JWT/auth context
        notes=data.notes,
    )
    
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)
    
    logger.info(f"API Key created: {api_key_obj.system_identifier}")
    
    return _ensure_api_key_defaults(api_key_obj)


@router.get("", response_model=List[HL7v2APIKeyListResponse])
async def list_api_keys(
    active_only: bool = False,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Lista todas as API Keys.
    
    Args:
        active_only: Se True, retorna apenas keys ativas
        db: Sessão do banco de dados
    
    Returns:
        List[HL7v2APIKeyListResponse]: Lista de API Keys (sem a key em si)
    """
    stmt = select(HL7v2APIKey).order_by(HL7v2APIKey.created_at.desc())
    
    if active_only:
        stmt = stmt.where(HL7v2APIKey.is_active == True)
    
    result = await db.execute(stmt)
    api_keys = result.scalars().all()
    
    return [_ensure_api_key_defaults(item) for item in api_keys]


@router.get("/{api_key_id}", response_model=HL7v2APIKeyListResponse)
async def get_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Obtém detalhes de uma API Key específica.
    
    Args:
        api_key_id: ID da API Key
        db: Sessão do banco de dados
    
    Returns:
        HL7v2APIKeyListResponse: Detalhes da API Key (sem a key em si)
    """
    stmt = select(HL7v2APIKey).where(HL7v2APIKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID {api_key_id} not found",
        )
    
    return _ensure_api_key_defaults(api_key)


@router.patch("/{api_key_id}", response_model=HL7v2APIKeyListResponse)
async def update_api_key(
    api_key_id: int,
    data: HL7v2APIKeyUpdate,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Atualiza uma API Key.
    
    Args:
        api_key_id: ID da API Key
        data: Dados para atualizar
        db: Sessão do banco de dados
    
    Returns:
        HL7v2APIKeyListResponse: API Key atualizada
    """
    stmt = select(HL7v2APIKey).where(HL7v2APIKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID {api_key_id} not found",
        )
    
    # Atualizar campos
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(api_key, field, value)
    
    await db.commit()
    await db.refresh(api_key)
    
    logger.info(f"API Key updated: {api_key.system_identifier}")

    return _ensure_api_key_defaults(api_key)


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Deleta uma API Key.

    ⚠️  CUIDADO: Esta ação é irreversível!

    Args:
        api_key_id: ID da API Key
        db: Sessão do banco de dados
    """
    stmt = select(HL7v2APIKey).where(HL7v2APIKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID {api_key_id} not found",
        )

    await db.delete(api_key)
    await db.commit()

    logger.warning(f"API Key deleted: {api_key.system_identifier}")


# ─────────────────────────────────────────────────────────────────────────────
# IP Whitelist Management
# ─────────────────────────────────────────────────────────────────────────────


@router.get("/{api_key_id}/whitelist", response_model=IPWhitelistResponse)
async def get_ip_whitelist(
    api_key_id: int,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Obtém a whitelist de IPs de uma API Key.

    Args:
        api_key_id: ID da API Key
        db: Sessão do banco de dados

    Returns:
        IPWhitelistResponse: Whitelist de IPs
    """
    stmt = select(HL7v2APIKey).where(HL7v2APIKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID {api_key_id} not found",
        )

    ip_count = 0
    if api_key.allowed_ips:
        ip_count = len([ip.strip() for ip in api_key.allowed_ips.split(',') if ip.strip()])

    return IPWhitelistResponse(
        api_key_id=api_key.id,
        system_identifier=api_key.system_identifier,
        allowed_ips=api_key.allowed_ips,
        ip_count=ip_count,
    )


@router.post("/{api_key_id}/whitelist/add", response_model=IPWhitelistResponse)
async def add_ips_to_whitelist(
    api_key_id: int,
    data: IPWhitelistAddRequest,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Adiciona IPs à whitelist de uma API Key.

    Suporta IPs individuais e notação CIDR (ex: 192.168.1.0/24).

    Args:
        api_key_id: ID da API Key
        data: IPs para adicionar
        db: Sessão do banco de dados

    Returns:
        IPWhitelistResponse: Whitelist atualizada
    """
    stmt = select(HL7v2APIKey).where(HL7v2APIKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID {api_key_id} not found",
        )

    # Parse new IPs
    new_ips = [ip.strip() for ip in data.ips.split(',') if ip.strip()]

    # Get existing IPs
    existing_ips = []
    if api_key.allowed_ips:
        existing_ips = [ip.strip() for ip in api_key.allowed_ips.split(',') if ip.strip()]

    # Merge (avoid duplicates)
    all_ips = list(set(existing_ips + new_ips))

    # Update
    api_key.allowed_ips = ','.join(all_ips)
    await db.commit()
    await db.refresh(api_key)

    logger.info(f"IPs added to whitelist for {api_key.system_identifier}: {new_ips}")

    return IPWhitelistResponse(
        api_key_id=api_key.id,
        system_identifier=api_key.system_identifier,
        allowed_ips=api_key.allowed_ips,
        ip_count=len(all_ips),
    )


@router.post("/{api_key_id}/whitelist/remove", response_model=IPWhitelistResponse)
async def remove_ips_from_whitelist(
    api_key_id: int,
    data: IPWhitelistRemoveRequest,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Remove IPs da whitelist de uma API Key.

    Args:
        api_key_id: ID da API Key
        data: IPs para remover
        db: Sessão do banco de dados

    Returns:
        IPWhitelistResponse: Whitelist atualizada
    """
    stmt = select(HL7v2APIKey).where(HL7v2APIKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID {api_key_id} not found",
        )

    # Parse IPs to remove
    ips_to_remove = [ip.strip() for ip in data.ips.split(',') if ip.strip()]

    # Get existing IPs
    existing_ips = []
    if api_key.allowed_ips:
        existing_ips = [ip.strip() for ip in api_key.allowed_ips.split(',') if ip.strip()]

    # Remove
    remaining_ips = [ip for ip in existing_ips if ip not in ips_to_remove]

    # Update
    api_key.allowed_ips = ','.join(remaining_ips) if remaining_ips else None
    await db.commit()
    await db.refresh(api_key)

    logger.info(f"IPs removed from whitelist for {api_key.system_identifier}: {ips_to_remove}")

    return IPWhitelistResponse(
        api_key_id=api_key.id,
        system_identifier=api_key.system_identifier,
        allowed_ips=api_key.allowed_ips,
        ip_count=len(remaining_ips),
    )


@router.delete("/{api_key_id}/whitelist", response_model=IPWhitelistResponse)
async def clear_ip_whitelist(
    api_key_id: int,
    db: AsyncSession = Depends(_get_db_session_dependency),
):
    """Limpa completamente a whitelist de IPs de uma API Key.

    Após esta operação, todos os IPs serão permitidos.

    Args:
        api_key_id: ID da API Key
        db: Sessão do banco de dados

    Returns:
        IPWhitelistResponse: Whitelist vazia
    """
    stmt = select(HL7v2APIKey).where(HL7v2APIKey.id == api_key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API Key with ID {api_key_id} not found",
        )

    api_key.allowed_ips = None
    await db.commit()
    await db.refresh(api_key)

    logger.warning(f"IP whitelist cleared for {api_key.system_identifier}")

    return IPWhitelistResponse(
        api_key_id=api_key.id,
        system_identifier=api_key.system_identifier,
        allowed_ips=None,
        ip_count=0,
    )
