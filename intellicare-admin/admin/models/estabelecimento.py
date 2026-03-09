"""Modelo Estabelecimento (unidade de saúde: hospital, UBS, etc.)."""

from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.sql import func
import uuid
import os

from admin.db import Base

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}


class Estabelecimento(Base):
    __tablename__ = "estabelecimentos"
    __table_args__ = TABLE_ARGS

    id = Column(String(50), primary_key=True)
    cnes = Column(String(20), unique=True, nullable=False)
    nome = Column(String(255), nullable=False)
    alias = Column(String(100))
    endereco = Column(String(500))
    cidade = Column(String(100))
    estado = Column(String(2))
    cep = Column(String(10))
    telefone = Column(String(30))
    tenant_id = Column(String(50))
    active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
