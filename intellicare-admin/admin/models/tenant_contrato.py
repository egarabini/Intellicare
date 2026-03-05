from uuid import uuid4, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Numeric, DateTime, Date, Text
from sqlalchemy.sql import func
from datetime import datetime, date
from decimal import Decimal

from admin.db import Base

class TenantContrato(Base):
    __tablename__ = "tenant_contratos"
    __table_args__ = {"schema": "platform"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("platform.tenants.tenant_id"))
    plan_id: Mapped[UUID] = mapped_column(ForeignKey("platform.plans.id"))
    inicio_vigencia: Mapped[date] = mapped_column(Date)
    fim_vigencia: Mapped[date | None] = mapped_column(Date, nullable=True)
    valor_mensal: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    obs: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
