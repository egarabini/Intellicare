"""
SQLAlchemy Models for Florence Anonymization

LGPD-compliant data models for anonymized patient data
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, LargeBinary, ForeignKey, Index, Numeric
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PacienteAnonimizado(Base):
    """
    Paciente com dados anonimizados ya inseridos
    
    Propriedade: Nunca contém dados PII
    Apenas: Hash do CPF, Nome truncado, Data mes/ano
    """
    __tablename__ = "paciente"
    
    # Identificador = Hash do CPF (SHA256 = 64 hex caracteres)
    paciente_id_hash = Column(String(64), primary_key=True, index=True)
    
    # Dados anonimizados (nunca PII)
    nome_truncado = Column(String(50), nullable=True)  # "João S."
    data_nascimento_mes_ano = Column(String(7), nullable=True)  # "01/1980"
    sexo = Column(String(1), nullable=True)  # "M" ou "F"
    
    # Dados clínicos (não são PII)
    altura_cm = Column(Integer, nullable=True)
    peso_kg = Column(Numeric(5, 2), nullable=True)
    
    # Auditoria
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    exames = relationship("Exame", back_populates="paciente", cascade="all, delete-orphan")
    acessos = relationship("AcessoHashMapping", back_populates="paciente", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Paciente hash={self.paciente_id_hash[:16]}...>"
    
    def __str__(self) -> str:
        return f"Paciente(nome='{self.nome_truncado}', dob='{self.data_nascimento_mes_ano}')"


class PacienteHashMapping(Base):
    """
    Mapeamento CPF original → Hash (ENCRIPTADO)
    
    ⚠️ SEGURANÇA CRÍTICA
    - Deve estar em banco SEPARADO (idealmente)
    - Encriptação AES-256 do CPF original
    - Acesso é loggado em AcessoHashMapping
    - Queries nunca devem expor CPF_original
    - Soft delete implementado
    """
    __tablename__ = "paciente_hash_mapping"
    
    # Hash do CPF é chave primária
    cpf_hash = Column(String(64), primary_key=True, index=True)
    
    # CPF original criptografado (AES-256)
    # ⚠️ Nunca é retornado em queries, apenas usado para verificação interna
    cpf_aes256_encrypted = Column(LargeBinary, nullable=False)
    
    # Auditoria de acesso
    last_accessed_by = Column(String(100), nullable=True)
    last_accessed_at = Column(DateTime, nullable=True)
    accessed_count = Column(Integer, default=0)
    
    # Soft-delete (não apagar, apenas marcar como deletado)
    is_deleted = Column(Boolean, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    deleted_by = Column(String(100), nullable=True)
    
    # Rastreamento
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index('idx_deleted_acesso', 'is_deleted', 'last_accessed_at'),
    )
    
    def __repr__(self) -> str:
        status = "DELETADO" if self.is_deleted else "ATIVO"
        return f"<Mapping hash={self.cpf_hash[:16]}... {status}>"


class AcessoHashMapping(Base):
    """
    Log de auditoria para CADA acesso a PII
    
    LGPD Art. 6: Rastreabilidade obrigatória
    
    Registra:
    - Quem acessou (usuario_id)
    - Quando (accessed_at)
    - Por que (motivo_acesso)
    - Resultado (sucesso/erro)
    """
    __tablename__ = "auditoria_acesso_pii"
    
    # Chave primária auto-incrementada
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Referência ao mapeamento acessado
    cpf_hash = Column(
        String(64),
        ForeignKey("paciente_hash_mapping.cpf_hash"),
        nullable=False,
        index=True
    )
    
    # Quem acessou
    usuario_id = Column(String(100), nullable=False, index=True)
    usuario_ip = Column(String(45), nullable=False)  # IPv4 ou IPv6
    usuario_user_agent = Column(String(500), nullable=True)
    
    # Quando
    accessed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # O quê (justificativa)
    motivo_acesso = Column(String(500), nullable=True)  # "Resgate de CPF para SMS"
    
    # Resultado
    sucesso = Column(Boolean, default=True, index=True)
    erro_msg = Column(String(500), nullable=True)
    
    # Relacionamentos
    paciente_hash = relationship(
        "PacienteHashMapping",
        backref="acessos_auditoria"
    )
    paciente = relationship(
        "PacienteAnonimizado",
        back_populates="acessos"
    )
    
    __table_args__ = (
        Index('idx_auditoria_usuario_data', 'usuario_id', 'accessed_at'),
        Index('idx_auditoria_sucesso', 'sucesso', 'accessed_at'),
    )
    
    def __repr__(self) -> str:
        status = "✅" if self.sucesso else "❌"
        return f"<Acesso {status} hash={self.cpf_hash[:16]}... by {self.usuario_id}>"


class Exame(Base):
    """
    Placeholder para Exame (será implementado no Technical Spec)
    
    Relacionamento com Paciente anonimizado
    """
    __tablename__ = "exame"
    
    id = Column(Integer, primary_key=True)
    paciente_id_hash = Column(
        String(64),
        ForeignKey("paciente.paciente_id_hash"),
        nullable=False,
        index=True
    )
    tipo = Column(String(100), nullable=False)
    data_exame = Column(DateTime, default=datetime.utcnow)
    
    paciente = relationship("PacienteAnonimizado", back_populates="exames")


# Export para uso em migrações e serviços
__all__ = [
    "Base",
    "PacienteAnonimizado",
    "PacienteHashMapping",
    "AcessoHashMapping",
    "Exame",
]
