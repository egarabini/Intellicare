from pydantic import BaseModel, ConfigDict
from datetime import datetime, date
from uuid import UUID
from typing import Optional
from decimal import Decimal

class BillingRecordCreate(BaseModel):
    estabelecimento_id: UUID
    periodo_ano: int
    periodo_mes: int
    gestores_ativos: int = 0
    usuarios_saude_ativos: int = 0
    chamadas_api: int = 0
    storage_gb: Decimal = Decimal('0.0')
    preco_base: Decimal
    preco_excedente: Decimal = Decimal('0.0')
    preco_total: Decimal
    status: str = "pending"
    pago_em: Optional[datetime] = None
    data_vencimento: Optional[date] = None

class BillingRecordResponse(BillingRecordCreate):
    id: UUID
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
