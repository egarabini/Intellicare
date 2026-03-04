from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Numeric, Text, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from admin.db import Base

import os

SCHEMA = os.getenv("DB_SCHEMA", "platform")
TABLE_ARGS = {"schema": SCHEMA} if SCHEMA else {}

class Estabelecimento(Base):
    __tablename__ = "estabelecimentos"
    __table_args__ = TABLE_ARGS

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = Column(String(255), nullable=False)
    cnes = Column(String(15), unique=True)  # CNES do DATASUS
    cnpj = Column(String(14), unique=True)
    tipo = Column(String(50), nullable=False)  # HOSPITAL, CLINICA, LABORATORIO, SECRETARIA
    logo_url = Column(String(512))
    status = Column(String(50), default="provisioning")  # provisioning, active, suspended, cancelled

    # Contato do gestor principal
    gestor_nome = Column(String(255))
    gestor_email = Column(String(255))
    gestor_telefone = Column(String(20))

    # Configurações
    configuracoes = Column(JSON, default=dict)

    # Plano
    plano_id = Column(String(50), ForeignKey(f"{SCHEMA}.planos.id" if SCHEMA else "planos.id"))

    # Metadata
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
    criado_por = Column(UUID(as_uuid=True))
    provisionado_em = Column(DateTime(timezone=True))
    suspenso_em = Column(DateTime(timezone=True))
    cancelado_em = Column(DateTime(timezone=True))

    rowversion = Column(Integer, default=1)

    # Relationships
    plano = relationship("Plano", backref="estabelecimentos")
    gestores = relationship("Gestor", back_populates="estabelecimento")


class Gestor(Base):
    __tablename__ = "gestores"
    __table_args__ = TABLE_ARGS

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estabelecimento_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.estabelecimentos.id" if SCHEMA else "estabelecimentos.id"))
    usuario_keycloak_id = Column(UUID(as_uuid=True), nullable=False)
    nome = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    permissoes = Column(JSON, default=dict)  # {"pode_gerenciar_usuarios": true, ...}
    ativo = Column(Boolean, default=True)

    # Metadata
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    criado_por = Column(UUID(as_uuid=True))

    # Relationship
    estabelecimento = relationship("Estabelecimento", back_populates="gestores")


class Plano(Base):
    __tablename__ = "planos"
    __table_args__ = TABLE_ARGS

    id = Column(String(50), primary_key=True)  # trial, basico, profissional, enterprise
    nome = Column(String(255), nullable=False)
    descricao = Column(Text)
    preco_mensal = Column(Numeric(10, 2))
    moeda = Column(String(3), default="BRL")

    # Limites
    max_gestores = Column(Integer)
    max_usuarios_saude = Column(Integer)
    max_storage_gb = Column(Integer)
    max_chamadas_api_mensal = Column(Integer)

    # Módulos incluídos
    modulos = Column(JSON, default=list)  # ["florence", "oswaldo", "wanda"]

    status = Column(String(50), default="active")
    criado_em = Column(DateTime(timezone=True), server_default=func.now())


class ModuloPorEstabelecimento(Base):
    __tablename__ = "modulos_estabelecimento"
    __table_args__ = (
        UniqueConstraint('estabelecimento_id', 'modulo', name='uq_tenant_modulo'),
        TABLE_ARGS
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    estabelecimento_id = Column(UUID(as_uuid=True), ForeignKey(f"{SCHEMA}.estabelecimentos.id" if SCHEMA else "estabelecimentos.id"))
    modulo = Column(String(100), nullable=False)
    habilitado = Column(Boolean, default=True)
    configuracao = Column(JSON, default=dict)

    estabelecimento = relationship("Estabelecimento", backref="modulos")
