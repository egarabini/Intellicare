"""
Pillar model - 7 Pilares de Donabedian (1990).

Tabela de referência com 7 registros fixos:
1. Eficácia (Efficacy)
2. Efetividade (Effectiveness)
3. Eficiência (Efficiency)
4. Otimidade (Optimality)
5. Aceitabilidade (Acceptability)
6. Legitimidade (Legitimacy)
7. Equidade (Equity)

FASE 2: Updated with audit metadata, UUID primary key, soft delete, and optimistic locking.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID as PythonUUID

from sqlalchemy import String, Integer, DateTime, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from donabedian.models import Base


class Pillar(Base):
    """
    Pillar model representing the 7 pillars of quality by Donabedian.
    
    This is a reference table with 7 fixed records loaded from seed data.
    Features:
    - UUID primary key (distributed systems compatible)
    - Audit metadata (created_by, created_at, updated_by, updated_at)
    - Soft delete (valid_to for data retention)
    - Optimistic locking (rowversion for concurrent update detection)
    """
    
    __tablename__ = "pilares"
    
    # Primary Key (FASE 2: UUID instead of autoincrement)
    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
        comment="Unique identifier (UUID) for distributed systems"
    )
    
    # Business Fields
    nome: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Pillar name (efficacy, effectiveness, efficiency, optimality, acceptability, legitimacy, equity)"
    )
    
    descricao: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Pillar description in Portuguese"
    )
    
    tipo: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Pillar type: ESTRUTURA, PROCESSO, RESULTADO"
    )
    
    ordem_exibicao: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Display order (1-7)"
    )
    
    ativo: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether this pillar is active"
    )
    
    # ========================================================================
    # AUDIT METADATA (REQUIRED - FASE 2)
    # ========================================================================
    
    created_by: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="User ID who created this record"
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when record was created"
    )
    
    updated_by: Mapped[Optional[PythonUUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="User ID who last updated this record"
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default="NOW()",
        comment="Timestamp when record was last updated"
    )
    
    # ========================================================================
    # SOFT DELETE (REQUIRED - FASE 2)
    # ========================================================================
    
    valid_to: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp (NULL = active)"
    )
    
    # ========================================================================
    # OPTIMISTIC LOCKING (REQUIRED - FASE 2)
    # ========================================================================
    
    rowversion: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
        comment="Row version for optimistic locking (incremented on UPDATE)"
    )
    
    # Constraint: valid_to must be after created_at if set
    __table_args__ = (
        CheckConstraint('valid_to IS NULL OR valid_to > created_at', name='ck_pillar_valid_to'),
    )
    
    # ========================================================================
    # RELATIONSHIPS
    # ========================================================================
    
    indicator_pillars: Mapped[List["IndicatorPillar"]] = relationship(
        "IndicatorPillar",
        back_populates="pillar",
        cascade="all, delete-orphan",
        foreign_keys="IndicatorPillar.pillar_id"
    )
    
    # ========================================================================
    # METHODS
    # ========================================================================
    
    def __repr__(self) -> str:
        return f"<Pillar(id={self.id}, nome='{self.nome}', tipo='{self.tipo}', ativo={self.ativo})>"
    
    def __str__(self) -> str:
        return self.nome
    
    def is_deleted(self) -> bool:
        """Check if this record is soft-deleted."""
        return self.valid_to is not None

