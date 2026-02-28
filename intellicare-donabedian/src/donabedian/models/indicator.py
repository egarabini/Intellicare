"""
Indicator model - Indicadores de qualidade assistencial.

Representa indicadores que podem estar associados a múltiplos pilares
através da tabela IndicatorPillar (N:N).

FASE 2: Updated with audit metadata, UUID primary key, soft delete, and optimistic locking.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID as PythonUUID
import enum

from sqlalchemy import String, Integer, Float, DateTime, Enum as SQLEnum, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from donabedian.models import Base


class TriadDimension(str, enum.Enum):
    """Dimensões da tríade de Donabedian."""
    STRUCTURE = "structure"  # Estrutura (recursos)
    PROCESS = "process"      # Processo (atividades)
    OUTCOME = "outcome"      # Resultado (desfechos)


class TargetOperator(str, enum.Enum):
    """Operadores de comparação para metas."""
    GREATER_EQUAL = ">="  # Meta é atingida se valor >= target
    LESS_EQUAL = "<="     # Meta é atingida se valor <= target
    EQUAL = "=="          # Meta é atingida se valor == target


class Indicator(Base):
    """
    Indicator model representing quality indicators.
    
    Each indicator can be associated with multiple pillars through
    the IndicatorPillar table (N:N relationship with weights).
    
    Features:
    - UUID primary key (distributed systems compatible)
    - Audit metadata (created_by, created_at, updated_by, updated_at)
    - Soft delete (valid_to for data retention)
    - Optimistic locking (rowversion for concurrent update detection)
    """
    
    __tablename__ = "indicadores"
    
    # Primary Key (FASE 2: UUID instead of autoincrement)
    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default="gen_random_uuid()",
        comment="Unique identifier (UUID)"
    )
    
    # Basic Information
    nome: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        comment="Indicator name"
    )
    
    descricao: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        comment="Detailed description of the indicator"
    )
    
    formula: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Calculation formula (e.g., 'numerator / denominator * 100')"
    )
    
    unidade: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Unit of measurement (%, days, count, etc.)"
    )
    
    # Target Configuration
    valor_meta: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        comment="Target value to be achieved"
    )
    
    operador_meta: Mapped[TargetOperator] = mapped_column(
        SQLEnum(TargetOperator, native_enum=False, length=20),
        nullable=False,
        default=TargetOperator.GREATER_EQUAL,
        comment="Comparison operator for target (>=, <=, ==)"
    )
    
    # Triad Classification
    dimensao_triado: Mapped[TriadDimension] = mapped_column(
        SQLEnum(TriadDimension, native_enum=False, length=20),
        nullable=False,
        comment="Donabedian triad dimension (structure, process, outcome)"
    )
    
    ativo: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment="Whether this indicator is active"
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
        comment="Row version for optimistic locking"
    )
    
    # Constraint: valid_to must be after created_at if set
    __table_args__ = (
        CheckConstraint('valid_to IS NULL OR valid_to > created_at', name='ck_indicator_valid_to'),
    )
    
    # Relationships
    indicator_pillars: Mapped[List["IndicatorPillar"]] = relationship(
        "IndicatorPillar",
        back_populates="indicator",
        cascade="all, delete-orphan",
        foreign_keys="IndicatorPillar.indicator_id"
    )
    
    measurements: Mapped[List["Measurement"]] = relationship(
        "Measurement",
        back_populates="indicator",
        cascade="all, delete-orphan",
        foreign_keys="Measurement.indicator_id"
    )
    
    def __repr__(self) -> str:
        return f"<Indicator(id={self.id}, nome='{self.nome}', dimensao='{self.dimensao_triado.value}')>"
    
    def __str__(self) -> str:
        return self.nome
    
    def is_deleted(self) -> bool:
        """Check if this record is soft-deleted."""
        return self.valid_to is not None

