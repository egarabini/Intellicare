import asyncio
import logging
from datetime import datetime

from admin.db import async_session_maker
from admin.services.billing_service import BillingService
from admin.services.tenant_service import TenantRepository

logger = logging.getLogger(__name__)

async def run_monthly_billing_cycle():
    """
    Worker agendado (ex: rodar dia 1 de cada mes).
    Processa todos os tenants ativos e gera as faturas.
    """
    logger.info("Iniciando ciclo de faturamento mensal...")
    ano = datetime.now().year
    mes = datetime.now().month
    
    # Se roda dia 1, normalmente fatura o mês anterior
    if mes == 1:
        mes = 12
        ano -= 1
    else:
        mes -= 1

    async with async_session_maker() as session:
        tenant_repo = TenantRepository(session)
        billing_service = BillingService(session)
        
        # Pega todos os tenants (ideal seria buscar em batches para milhões de usuários)
        skip = 0
        limit = 100
        while True:
            tenants = await tenant_repo.list_tenants(skip=skip, limit=limit)
            if not tenants:
                break
                
            for tenant in tenants:
                if tenant.status in ("active", "suspended"):
                    try:
                        await billing_service.calculate_monthly_billing(tenant.id, ano, mes)
                        logger.info(f"Faturado tenant {tenant.id} para {ano}/{mes}")
                    except Exception as e:
                        logger.error(f"Erro ao faturar tenant {tenant.id}: {e}")
            
            await session.commit()
            skip += limit
            
    logger.info("Ciclo de faturamento concluído.")

if __name__ == "__main__":
    asyncio.run(run_monthly_billing_cycle())
