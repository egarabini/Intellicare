from typing import List, Optional
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from admin.models.billing import RegistroBilling
from admin.models.tenant import Estabelecimento


class BillingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def calculate_monthly_billing(self, tenant_id: UUID, ano: int, mes: int) -> RegistroBilling:
        """
        Calcula o faturamento do mês para o tenant.
        Na prática, leria uso de serviços, Keycloak (usuários), banco (storage), etc.
        Para este esqueleto, simula o processo e grava o registro.
        """
        # Obter tenant e plano
        tenant = await self.session.get(Estabelecimento, tenant_id)
        if not tenant:
            raise ValueError("Tenant não encontrado")
            
        # Mock do cálculo:
        # Preço base do plano 
        # (na prática, tenant.plano seria resolvido, aqui apenas mockando valor Fixo R$ 199.90)
        preco_base = Decimal("199.90")
        preco_excedente = Decimal("0.0")
        
        gestores_ativos = 1
        usuarios_saude_ativos = 5
        chamadas_api = 1050
        storage_gb = Decimal("1.2")

        preco_total = preco_base + preco_excedente

        # Cria ou atualiza o registro
        stmt = select(RegistroBilling).where(
            RegistroBilling.estabelecimento_id == tenant_id,
            RegistroBilling.periodo_ano == ano,
            RegistroBilling.periodo_mes == mes
        )
        result = await self.session.execute(stmt)
        record = result.scalars().first()

        if record:
            record.preco_base = preco_base
            record.preco_excedente = preco_excedente
            record.preco_total = preco_total
            record.gestores_ativos = gestores_ativos
            record.usuarios_saude_ativos = usuarios_saude_ativos
            record.chamadas_api = chamadas_api
            record.storage_gb = storage_gb
        else:
            record = RegistroBilling(
                estabelecimento_id=tenant_id,
                periodo_ano=ano,
                periodo_mes=mes,
                preco_base=preco_base,
                preco_excedente=preco_excedente,
                preco_total=preco_total,
                gestores_ativos=gestores_ativos,
                usuarios_saude_ativos=usuarios_saude_ativos,
                chamadas_api=chamadas_api,
                storage_gb=storage_gb,
                status="pending",
                data_vencimento=date(ano, mes, 10) # Vence dia 10
            )
            self.session.add(record)
            
        await self.session.flush()
        return record

    async def get_billing_history(self, tenant_id: UUID) -> List[RegistroBilling]:
        stmt = select(RegistroBilling).where(RegistroBilling.estabelecimento_id == tenant_id).order_by(RegistroBilling.periodo_ano.desc(), RegistroBilling.periodo_mes.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def mark_as_paid(self, billing_id: UUID) -> Optional[RegistroBilling]:
        record = await self.session.get(RegistroBilling, billing_id)
        if record:
            record.status = "paid"
            record.pago_em = datetime.now()
            await self.session.flush()
        return record
