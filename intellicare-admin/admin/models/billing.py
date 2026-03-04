from sqlalchemy import Column, String, DateTime, Integer, Numeric, ForeignKey, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from admin.db import Base

import os

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}

class RegistroBilling(Base):
    __tablename__ = "registro_billing"
    # The original code had __table_args__ defined twice.
    # The second definition was the effective one, combining UniqueConstraint and schema.
    # We'll update that effective definition.
    # __table_args__ = {"schema": "platform"} # This line was effectively overridden

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estabelecimento_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.estabelecimentos.id" if SCHEMA else "estabelecimentos.id"))
    periodo_ano = Column(Integer, nullable=False)
    periodo_mes = Column(Integer, nullable=False)

    # Uso
    gestores_ativos = Column(Integer, default=0)
    usuarios_saude_ativos = Column(Integer, default=0)
    chamadas_api = Column(Integer, default=0)
    storage_gb = Column(Numeric(10, 2), default=0)

    # Valores
    preco_base = Column(Numeric(10, 2))
    preco_excedente = Column(Numeric(10, 2), default=0)
    preco_total = Column(Numeric(10, 2))

    # Status
    status = Column(String(50), default="pending")  # pending, paid, overdue, cancelled
    pago_em = Column(DateTime(timezone=True))
    data_vencimento = Column(Date)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    estabelecimento = relationship("Estabelecimento", backref="registros_billing")
    __table_args__ = (
        UniqueConstraint("estabelecimento_id", "periodo_ano", "periodo_mes"),
        TABLE_ARGS
    )

