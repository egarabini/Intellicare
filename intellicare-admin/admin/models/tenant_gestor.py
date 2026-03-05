from uuid import uuid4, UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Boolean, DateTime
from sqlalchemy.sql import func
from datetime import datetime

from admin.db import Base

class TenantGestor(Base):
    __tablename__ = "tenant_gestores"
    __table_args__ = {"schema": "platform"}

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("platform.tenants.tenant_id"))
    keycloak_user_id: Mapped[str] = mapped_column(String(255), unique=True)
    nome: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    telefone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
