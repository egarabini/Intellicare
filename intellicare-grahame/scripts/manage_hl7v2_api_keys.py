#!/usr/bin/env python3
"""Script para gerenciar API Keys HL7v2.

Este script permite criar, listar, desabilitar e remover API Keys para
autenticação de sistemas legados hospitalares.

Uso:
    python scripts/manage_hl7v2_api_keys.py create --system "Hospital São Paulo" --identifier "HSP-TASY"
    python scripts/manage_hl7v2_api_keys.py list
    python scripts/manage_hl7v2_api_keys.py disable <api_key>
    python scripts/manage_hl7v2_api_keys.py delete <api_key>
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from grahame.config import config
from grahame.models.base import Base
from grahame.models.hl7v2_api_key import HL7v2APIKey


async def create_api_key(
    system_name: str,
    system_identifier: str,
    description: str = None,
    expires_days: int = None,
    rate_limit: int = 60,
    allowed_ips: str = None,
):
    """Create a new API Key.
    
    Args:
        system_name: Name of the system/hospital
        system_identifier: Unique identifier (e.g., HSP-TASY)
        description: Optional description
        expires_days: Days until expiration (None = never expires)
        rate_limit: Requests per minute (0 = no limit)
        allowed_ips: Comma-separated list of allowed IPs
    """
    engine = create_async_engine(config.grahame_database_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        # Generate API Key
        api_key = HL7v2APIKey.generate_api_key()
        
        # Calculate expiration
        expires_at = None
        if expires_days:
            expires_at = datetime.now(timezone.utc) + timedelta(days=expires_days)
        
        # Create API Key object
        api_key_obj = HL7v2APIKey(
            api_key=api_key,
            system_name=system_name,
            system_identifier=system_identifier,
            description=description,
            is_active=True,
            expires_at=expires_at,
            rate_limit_per_minute=rate_limit,
            allowed_ips=allowed_ips,
            created_by="admin",
        )
        
        session.add(api_key_obj)
        await session.commit()
        
        print(f"✅ API Key created successfully!")
        print(f"")
        print(f"System: {system_name}")
        print(f"Identifier: {system_identifier}")
        print(f"API Key: {api_key}")
        print(f"Expires: {expires_at.isoformat() if expires_at else 'Never'}")
        print(f"Rate Limit: {rate_limit} req/min")
        print(f"Allowed IPs: {allowed_ips or 'All'}")
        print(f"")
        print(f"⚠️  IMPORTANT: Save this API Key securely. It cannot be retrieved later!")
        print(f"")
        print(f"Usage:")
        print(f"  curl -X POST http://localhost:8012/api/v1/hl7v2/adt-a04 \\")
        print(f"    -H 'X-API-Key: {api_key}' \\")
        print(f"    -H 'Content-Type: application/x-hl7-v2' \\")
        print(f"    --data-binary @message.hl7")
    
    await engine.dispose()


async def list_api_keys():
    """List all API Keys."""
    engine = create_async_engine(config.grahame_database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        stmt = select(HL7v2APIKey).order_by(HL7v2APIKey.created_at.desc())
        result = await session.execute(stmt)
        api_keys = result.scalars().all()
        
        if not api_keys:
            print("No API Keys found.")
            return
        
        print(f"")
        print(f"{'ID':<5} {'System':<30} {'Identifier':<20} {'Status':<10} {'Expires':<20} {'Usage':<10}")
        print(f"{'-'*5} {'-'*30} {'-'*20} {'-'*10} {'-'*20} {'-'*10}")
        
        for key in api_keys:
            status = "Active" if key.is_valid() else "Inactive"
            expires = key.expires_at.strftime("%Y-%m-%d") if key.expires_at else "Never"
            usage = f"{key.usage_count} reqs"
            
            print(f"{key.id:<5} {key.system_name[:30]:<30} {key.system_identifier[:20]:<20} {status:<10} {expires:<20} {usage:<10}")
        
        print(f"")
    
    await engine.dispose()


async def disable_api_key(api_key: str):
    """Disable an API Key.
    
    Args:
        api_key: API Key to disable
    """
    engine = create_async_engine(config.grahame_database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_factory() as session:
        stmt = select(HL7v2APIKey).where(HL7v2APIKey.api_key == api_key)
        result = await session.execute(stmt)
        api_key_obj = result.scalar_one_or_none()
        
        if not api_key_obj:
            print(f"❌ API Key not found: {api_key}")
            return
        
        api_key_obj.is_active = False
        await session.commit()
        
        print(f"✅ API Key disabled: {api_key_obj.system_identifier}")
    
    await engine.dispose()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage HL7v2 API Keys")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create a new API Key")
    create_parser.add_argument("--system", required=True, help="System name (e.g., 'Hospital São Paulo')")
    create_parser.add_argument("--identifier", required=True, help="System identifier (e.g., 'HSP-TASY')")
    create_parser.add_argument("--description", help="Description")
    create_parser.add_argument("--expires-days", type=int, help="Days until expiration")
    create_parser.add_argument("--rate-limit", type=int, default=60, help="Requests per minute (default: 60)")
    create_parser.add_argument("--allowed-ips", help="Comma-separated list of allowed IPs")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all API Keys")
    
    # Disable command
    disable_parser = subparsers.add_parser("disable", help="Disable an API Key")
    disable_parser.add_argument("api_key", help="API Key to disable")
    
    args = parser.parse_args()
    
    if args.command == "create":
        asyncio.run(create_api_key(
            system_name=args.system,
            system_identifier=args.identifier,
            description=args.description,
            expires_days=args.expires_days,
            rate_limit=args.rate_limit,
            allowed_ips=args.allowed_ips,
        ))
    elif args.command == "list":
        asyncio.run(list_api_keys())
    elif args.command == "disable":
        asyncio.run(disable_api_key(args.api_key))
    else:
        parser.print_help()

