from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from gestor.db import get_db
from gestor.middleware import require_permission
from gestor.models.user import TenantUser
from gestor.models.sector import Sector
from gestor.models.settings import TenantSetting

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("")
@require_permission("gestor.dashboard") # Ou algo associado a admin local
async def get_dashboard_metrics(request: Request, db: AsyncSession = Depends(get_db)):
    """Retorna métricas básicas para o dashboard do gestor local."""
    
    # Exemplo: Número de usuários ativos
    users_result = await db.execute(select(func.count(TenantUser.id)).where(TenantUser.active == True))
    active_users = users_result.scalar_one_or_none() or 0
    
    # Exemplo: Número total de setores organizacionais
    sectors_result = await db.execute(select(func.count(Sector.id)).where(Sector.active == True))
    active_sectors = sectors_result.scalar_one_or_none() or 0

    return {
        "metrics": {
            "active_users": active_users,
            "active_sectors": active_sectors
        }
    }
