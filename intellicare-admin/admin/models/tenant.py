"""Admin Platform Models aligned with Tenant Schemas."""

from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import os

from admin.db import Base

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}

class Tenant(Base):
    __tablename__ = "tenants"
    __table_args__ = TABLE_ARGS

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String(50), unique=True, nullable=False)  # short unique id
    nome_fantasia = Column(String(255), nullable=False)
    razao_social = Column(String(255), nullable=False)
    cnpj = Column(String(18), unique=True, nullable=False)
    email_admin = Column(String(255), nullable=False)
    
    logo_url = Column(String(512))
    cor_primaria = Column(String(7), default="#1E88E5")
    cor_secundaria = Column(String(7), default="#43A047")
    dominio_custom = Column(String(255))

    status = Column(String(50), default="provisioning")
    provisioned = Column(Boolean, default=False)

    max_users = Column(Integer, default=50)
    max_sms_month = Column(Integer, default=0)

    # Reference to Plan
    plan_name = Column(String(50), ForeignKey(f"{SCHEMA}.plans.id" if SCHEMA else "plans.id"), default="trial")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    trial_expires_at = Column(DateTime(timezone=True))

    criado_por = Column(String(255))

    # Relationships
    modules = relationship("TenantModule", back_populates="tenant", lazy="joined")
    plan = relationship("Plan")


class Plan(Base):
    __tablename__ = "plans"
    __table_args__ = TABLE_ARGS

    id = Column(String(50), primary_key=True)  # trial, basico, profissional, enterprise
    nome = Column(String(255), nullable=False)
    descricao = Column(String(512))
    preco_mensal = Column(Integer)  # Em centavos
    moeda = Column(String(3), default="BRL")
    
    status = Column(String(50), default="active")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class TenantModule(Base):
    __tablename__ = "tenant_modules"
    __table_args__ = (
        UniqueConstraint('tenant_id', 'module_name', name='uq_tenant_module'),
        TABLE_ARGS
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.tenants.id" if SCHEMA else "tenants.id"))
    module_name = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True)
    config_json = Column(JSON, default=dict)
    
    activated_at = Column(DateTime(timezone=True), server_default=func.now())

    tenant = relationship("Tenant", back_populates="modules")
